import errno
import locale
import os
import struct
import sys
import threading
import time
import signal
from subprocess import Popen, PIPE
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    IO,
    List,
    Optional,
    Tuple,
    Type,
)

# Import some platform-specific things at top level so they can be mocked for
# tests.
try:
    import pty
except ImportError:
    pty = None  # type: ignore[assignment]
try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore[assignment]
try:
    import termios
except ImportError:
    termios = None  # type: ignore[assignment]

from .exceptions import (
    UnexpectedExit,
    Failure,
    ThreadException,
    WatcherError,
    SubprocessPipeError,
    CommandTimedOut,
)
from .terminals import (
    WINDOWS,
    pty_size,
    character_buffered,
    ready_for_reading,
    bytes_to_read,
)
from .util import has_fileno, isatty, ExceptionHandlingThread

if TYPE_CHECKING:
    from .context import Context
    from .watchers import StreamWatcher


class Runner:
    """
    Partially-abstract core command-running API.

    This class is not usable by itself and must be subclassed, implementing a
    number of methods such as `start`, `wait` and `returncode`. For a subclass
    implementation example, see the source code for `.Local`.

    .. versionadded:: 1.0
    """

    opts: Dict[str, Any]
    using_pty: bool
    read_chunk_size = 1000
    input_sleep = 0.01

    def __init__(self, context: "Context") -> None:
        """
        Create a new runner with a handle on some `.Context`.

        :param context:
            a `.Context` instance, used to transmit default options and provide
            access to other contextualized information (e.g. a remote-oriented
            `.Runner` might want a `.Context` subclass holding info about
            hostnames and ports.)

            .. note::
                The `.Context` given to `.Runner` instances **must** contain
                default config values for the `.Runner` class in question. At a
                minimum, this means values for each of the default
                `.Runner.run` keyword arguments such as ``echo`` and ``warn``.

        :raises exceptions.ValueError:
            if not all expected default values are found in ``context``.
        """
        #: The `.Context` given to the same-named argument of `__init__`.
        self.context = context
        #: A `threading.Event` signaling program completion.
        #:
        #: Typically set after `wait` returns. Some IO mechanisms rely on this
        #: to know when to exit an infinite read loop.
        self.program_finished = threading.Event()
        # I wish Sphinx would organize all class/instance attrs in the same
        # place. If I don't do this here, it goes 'class vars -> __init__
        # docstring -> instance vars' :( TODO: consider just merging class and
        # __init__ docstrings, though that's annoying too.
        #: How many bytes (at maximum) to read per iteration of stream reads.
        self.read_chunk_size = self.__class__.read_chunk_size
        # Ditto re: declaring this in 2 places for doc reasons.
        #: How many seconds to sleep on each iteration of the stdin read loop
        #: and other otherwise-fast loops.
        self.input_sleep = self.__class__.input_sleep
        #: Whether pty fallback warning has been emitted.
        self.warned_about_pty_fallback = False
        #: A list of `.StreamWatcher` instances for use by `respond`. Is filled
        #: in at runtime by `run`.
        self.watchers: List["StreamWatcher"] = []
        # Optional timeout timer placeholder
        self._timer: Optional[threading.Timer] = None
        # Async flags (initialized for 'finally' referencing in case something
        # goes REAL bad during options parsing)
        self._asynchronous = False
        self._disowned = False

    def run(self, command: str, **kwargs: Any) -> Optional["Result"]:
        """
        Execute ``command``, returning an instance of `Result` once complete.

        By default, this method is synchronous (it only returns once the
        subprocess has completed), and allows interactive keyboard
        communication with the subprocess.

        It can instead behave asynchronously (returning early & requiring
        interaction with the resulting object to manage subprocess lifecycle)
        if you specify ``asynchronous=True``. Furthermore, you can completely
        disassociate the subprocess from Invoke's control (allowing it to
        persist on its own after Python exits) by saying ``disown=True``. See
        the per-kwarg docs below for details on both of these.

        .. note::
            All kwargs will default to the values found in this instance's
            `~.Runner.context` attribute, specifically in its configuration's
            ``run`` subtree (e.g. ``run.echo`` provides the default value for
            the ``echo`` keyword, etc). The base default values are described
            in the parameter list below.

        :param str command: The shell command to execute.

        :param bool asynchronous:
            When set to ``True`` (default ``False``), enables asynchronous
            behavior, as follows:

            - Connections to the controlling terminal are disabled, meaning you
              will not see the subprocess output and it will not respond to
              your keyboard input - similar to ``hide=True`` and
              ``in_stream=False`` (though explicitly given
              ``(out|err|in)_stream`` file-like objects will still be honored
              as normal).
            - `.run` returns immediately after starting the subprocess, and its
              return value becomes an instance of `Promise` instead of
              `Result`.
            - `Promise` objects are primarily useful for their `~Promise.join`
              method, which blocks until the subprocess exits (similar to
              threading APIs) and either returns a final `~Result` or raises an
              exception, just as a synchronous ``run`` would.

                - As with threading and similar APIs, users of
                  ``asynchronous=True`` should make sure to ``join`` their
                  `Promise` objects to prevent issues with interpreter
                  shutdown.
                - One easy way to handle such cleanup is to use the `Promise`
                  as a context manager - it will automatically ``join`` at the
                  exit of the context block.

            .. versionadded:: 1.4

        :param bool disown:
            When set to ``True`` (default ``False``), returns immediately like
            ``asynchronous=True``, but does not perform any background work
            related to that subprocess (it is completely ignored). This allows
            subprocesses using shell backgrounding or similar techniques (e.g.
            trailing ``&``, ``nohup``) to persist beyond the lifetime of the
            Python process running Invoke.

            .. note::
                If you're unsure whether you want this or ``asynchronous``, you
                probably want ``asynchronous``!

            Specifically, ``disown=True`` has the following behaviors:

            - The return value is ``None`` instead of a `Result` or subclass.
            - No I/O worker threads are spun up, so you will have no access to
              the subprocess' stdout/stderr, your stdin will not be forwarded,
              ``(out|err|in)_stream`` will be ignored, and features like
              ``watchers`` will not function.
            - No exit code is checked for, so you will not receive any errors
              if the subprocess fails to exit cleanly.
            - ``pty=True`` may not function correctly (subprocesses may not run
              at all; this seems to be a potential bug in Python's
              ``pty.fork``) unless your command line includes tools such as
              ``nohup`` or (the shell builtin) ``disown``.

            .. versionadded:: 1.4

        :param bool dry:
            Whether to dry-run instead of truly invoking the given command. See
            :option:`--dry` (which flips this on globally) for details on this
            behavior.

            .. versionadded:: 1.3

        :param bool echo:
            Controls whether `.run` prints the command string to local stdout
            prior to executing it. Default: ``False``.

            .. note::
                ``hide=True`` will override ``echo=True`` if both are given.

        :param echo_format:
            A string, which when passed to Python's inbuilt ``.format`` method,
            will change the format of the output when ``run.echo`` is set to
            true.

            Currently, only ``{command}`` is supported as a parameter.

            Defaults to printing the full command string in ANSI-escaped bold.

        :param bool echo_stdin:
            Whether to write data from ``in_stream`` back to ``out_stream``.

            In other words, in normal interactive usage, this parameter
            controls whether Invoke mirrors what you type back to your
            terminal.

            By default (when ``None``), this behavior is triggered by the
            following:

                * Not using a pty to run the subcommand (i.e. ``pty=False``),
                  as ptys natively echo stdin to stdout on their own;
                * And when the controlling terminal of Invoke itself (as per
                  ``in_stream``) appears to be a valid terminal device or TTY.
                  (Specifically, when `~invoke.util.isatty` yields a ``True``
                  result when given ``in_stream``.)

                  .. note::
                      This property tends to be ``False`` when piping another
                      program's output into an Invoke session, or when running
                      Invoke within another program (e.g. running Invoke from
                      itself).

            If both of those properties are true, echoing will occur; if either
            is false, no echoing will be performed.

            When not ``None``, this parameter will override that auto-detection
            and force, or disable, echoing.

        :param str encoding:
            Override auto-detection of which encoding the subprocess is using
            for its stdout/stderr streams (which defaults to the return value
            of `default_encoding`).

        :param err_stream:
            Same as ``out_stream``, except for standard error, and defaulting
            to ``sys.stderr``.

        :param dict env:
            By default, subprocesses receive a copy of Invoke's own environment
            (i.e. ``os.environ``). Supply a dict here to update that child
            environment.

            For example, ``run('command', env={'PYTHONPATH':
            '/some/virtual/env/maybe'})`` would modify the ``PYTHONPATH`` env
            var, with the rest of the child's env looking identical to the
            parent.

            .. seealso:: ``replace_env`` for changing 'update' to 'replace'.

        :param bool fallback:
            Controls auto-fallback behavior re: problems offering a pty when
            ``pty=True``. Whether this has any effect depends on the specific
            `Runner` subclass being invoked. Default: ``True``.

        :param hide:
            Allows the caller to disable ``run``'s default behavior of copying
            the subprocess' stdout and stderr to the controlling terminal.
            Specify ``hide='out'`` (or ``'stdout'``) to hide only the stdout
            stream, ``hide='err'`` (or ``'stderr'``) to hide only stderr, or
            ``hide='both'`` (or ``True``) to hide both streams.

            The default value is ``None``, meaning to print everything;
            ``False`` will also disable hiding.

            .. note::
                Stdout and stderr are always captured and stored in the
                ``Result`` object, regardless of ``hide``'s value.

            .. note::
                ``hide=True`` will also override ``echo=True`` if both are
                given (either as kwargs or via config/CLI).

        :param in_stream:
            A file-like stream object to used as the subprocess' standard
            input. If ``None`` (the default), ``sys.stdin`` will be used.

            If ``False``, will disable stdin mirroring entirely (though other
            functionality which writes to the subprocess' stdin, such as
            autoresponding, will still function.) Disabling stdin mirroring can
            help when ``sys.stdin`` is a misbehaving non-stream object, such as
            under test harnesses or headless command runners.

        :param out_stream:
            A file-like stream object to which the subprocess' standard output
            should be written. If ``None`` (the default), ``sys.stdout`` will
            be used.

        :param bool pty:
            By default, ``run`` connects directly to the invoked process and
            reads its stdout/stderr streams. Some programs will buffer (or even
            behave) differently in this situation compared to using an actual
            terminal or pseudoterminal (pty). To use a pty instead of the
            default behavior, specify ``pty=True``.

            .. warning::
                Due to their nature, ptys have a single output stream, so the
                ability to tell stdout apart from stderr is **not possible**
                when ``pty=True``. As such, all output will appear on
                ``out_stream`` (see below) and be captured into the ``stdout``
                result attribute. ``err_stream`` and ``stderr`` will always be
                empty when ``pty=True``.

        :param bool replace_env:
            When ``True``, causes the subprocess to receive the dictionary
            given to ``env`` as its entire shell environment, instead of
            updating a copy of ``os.environ`` (which is the default behavior).
            Default: ``False``.

        :param str shell:
            Which shell binary to use. Default: ``/bin/bash`` (on Unix;
            ``COMSPEC`` or ``cmd.exe`` on Windows.)

        :param timeout:
            Cause the runner to submit an interrupt to the subprocess and raise
            `.CommandTimedOut`, if the command takes longer than ``timeout``
            seconds to execute. Defaults to ``None``, meaning no timeout.

            .. versionadded:: 1.3

        :param bool warn:
            Whether to warn and continue, instead of raising
            `.UnexpectedExit`, when the executed command exits with a
            nonzero status. Default: ``False``.

            .. note::
                This setting has no effect on exceptions, which will still be
                raised, typically bundled in `.ThreadException` objects if they
                were raised by the IO worker threads.

                Similarly, `.WatcherError` exceptions raised by
                `.StreamWatcher` instances will also ignore this setting, and
                will usually be bundled inside `.Failure` objects (in order to
                preserve the execution context).

                Ditto `.CommandTimedOut` - basically, anything that prevents a
                command from actually getting to "exited with an exit code"
                ignores this flag.

        :param watchers:
            A list of `.StreamWatcher` instances which will be used to scan the
            program's ``stdout`` or ``stderr`` and may write into its ``stdin``
            (typically ``bytes`` objects) in response to patterns or other
            heuristics.

            See :doc:`/concepts/watchers` for details on this functionality.

            Default: ``[]``.

        :returns:
            `Result`, or a subclass thereof.

        :raises:
            `.UnexpectedExit`, if the command exited nonzero and
            ``warn`` was ``False``.

        :raises:
            `.Failure`, if the command didn't even exit cleanly, e.g. if a
            `.StreamWatcher` raised `.WatcherError`.

        :raises:
            `.ThreadException` (if the background I/O threads encountered
            exceptions other than `.WatcherError`).

        .. versionadded:: 1.0
        """
        try:
            return self._run_body(command, **kwargs)
        finally:
            if not (self._asynchronous or self._disowned):
                self.stop()

    def echo(self, command: str) -> None:
        print(self.opts["echo_format"].format(command=command))

    def _setup(self, command: str, kwargs: Any) -> None:
        """
        Prepare data on ``self`` so we're ready to start running.
        """
        # Normalize kwargs w/ config; sets self.opts, self.streams
        self._unify_kwargs_with_config(kwargs)
        # Environment setup
        self.env = self.generate_env(
            self.opts["env"], self.opts["replace_env"]
        )
        # Arrive at final encoding if neither config nor kwargs had one
        self.encoding = self.opts["encoding"] or self.default_encoding()
        # Echo running command (wants to be early to be included in dry-run)
        if self.opts["echo"]:
            self.echo(command)
        # Prepare common result args.
        # TODO: I hate this. Needs a deeper separate think about tweaking
        # Runner.generate_result in a way that isn't literally just this same
        # two-step process, and which also works w/ downstream.
        self.result_kwargs = dict(
            command=command,
            shell=self.opts["shell"],
            env=self.env,
            pty=self.using_pty,
            hide=self.opts["hide"],
            encoding=self.encoding,
        )

    def _run_body(self, command: str, **kwargs: Any) -> Optional["Result"]:
        # Prepare all the bits n bobs.
        self._setup(command, kwargs)
        # If dry-run, stop here.
        if self.opts["dry"]:
            return self.generate_result(
                **dict(self.result_kwargs, stdout="", stderr="", exited=0)
            )
        # Start executing the actual command (runs in background)
        self.start(command, self.opts["shell"], self.env)
        # If disowned, we just stop here - no threads, no timer, no error
        # checking, nada.
        if self._disowned:
            return None
        # Stand up & kick off IO, timer threads
        self.start_timer(self.opts["timeout"])
        self.threads, self.stdout, self.stderr = self.create_io_threads()
        for thread in self.threads.values():
            thread.start()
        # Wrap up or promise that we will, depending
        return self.make_promise() if self._asynchronous else self._finish()

    def make_promise(self) -> "Promise":
        """
        Return a `Promise` allowing async control of the rest of lifecycle.

        .. versionadded:: 1.4
        """
        return Promise(self)

    def _finish(self) -> "Result":
        # Wait for subprocess to run, forwarding signals as we get them.
        try:
            while True:
                try:
                    self.wait()
                    break  # done waiting!
                # Don't locally stop on ^C, only forward it:
                # - if remote end really stops, we'll naturally stop after
                # - if remote end does not stop (eg REPL, editor) we don't want
                # to stop prematurely
                except KeyboardInterrupt as e:
                    self.send_interrupt(e)
                # TODO: honor other signals sent to our own process and
                # transmit them to the subprocess before handling 'normally'.
        # Make sure we tie off our worker threads, even if something exploded.
        # Any exceptions that raised during self.wait() above will appear after
        # this block.
        finally:
            # Inform stdin-mirroring worker to stop its eternal looping
            self.program_finished.set()
            # Join threads, storing inner exceptions, & set a timeout if
            # necessary. (Segregate WatcherErrors as they are "anticipated
            # errors" that want to show up at the end during creation of
            # Failure objects.)
            watcher_errors = []
            thread_exceptions = []
            for target, thread in self.threads.items():
                thread.join(self._thread_join_timeout(target))
                exception = thread.exception()
                if exception is not None:
                    real = exception.value
                    if isinstance(real, WatcherError):
                        watcher_errors.append(real)
                    else:
                        thread_exceptions.append(exception)
        # If any exceptions appeared inside the threads, raise them now as an
        # aggregate exception object.
        # NOTE: this is kept outside the 'finally' so that main-thread
        # exceptions are raised before worker-thread exceptions; they're more
        # likely to be Big Serious Problems.
        if thread_exceptions:
            raise ThreadException(thread_exceptions)
        # Collate stdout/err, calculate exited, and get final result obj
        result = self._collate_result(watcher_errors)
        # Any presence of WatcherError from the threads indicates a watcher was
        # upset and aborted execution; make a generic Failure out of it and
        # raise that.
        if watcher_errors:
            # TODO: ambiguity exists if we somehow get WatcherError in *both*
            # threads...as unlikely as that would normally be.
            raise Failure(result, reason=watcher_errors[0])
        # If a timeout was requested and the subprocess did time out, shout.
        timeout = self.opts["timeout"]
        if timeout is not None and self.timed_out:
            raise CommandTimedOut(result, timeout=timeout)
        if not (result or self.opts["warn"]):
            raise UnexpectedExit(result)
        return result

    def _unify_kwargs_with_config(self, kwargs: Any) -> None:
        """
        Unify `run` kwargs with config options to arrive at local options.

        Sets:

        - ``self.opts`` - opts dict
        - ``self.streams`` - map of stream names to stream target values
        """
        opts = {}
        for key, value in self.context.config.run.items():
            runtime = kwargs.pop(key, None)
            opts[key] = value if runtime is None else runtime
        # Pull in command execution timeout, which stores config elsewhere,
        # but only use it if it's actually set (backwards compat)
        config_timeout = self.context.config.timeouts.command
        opts["timeout"] = kwargs.pop("timeout", config_timeout)
        # Handle invalid kwarg keys (anything left in kwargs).
        # Act like a normal function would, i.e. TypeError
        if kwargs:
            err = "run() got an unexpected keyword argument '{}'"
            raise TypeError(err.format(list(kwargs.keys())[0]))
        # Update disowned, async flags
        self._asynchronous = opts["asynchronous"]
        self._disowned = opts["disown"]
        if self._asynchronous and self._disowned:
            err = "Cannot give both 'asynchronous' and 'disown' at the same time!"  # noqa
            raise ValueError(err)
        # If hide was True, turn off echoing
        if opts["hide"] is True:
            opts["echo"] = False
        # Conversely, ensure echoing is always on when dry-running
        if opts["dry"] is True:
            opts["echo"] = True
        # Always hide if async
        if self._asynchronous:
            opts["hide"] = True
        # Then normalize 'hide' from one of the various valid input values,
        # into a stream-names tuple. Also account for the streams.
        out_stream, err_stream = opts["out_stream"], opts["err_stream"]
        opts["hide"] = normalize_hide(opts["hide"], out_stream, err_stream)
        # Derive stream objects
        if out_stream is None:
            out_stream = sys.stdout
        if err_stream is None:
            err_stream = sys.stderr
        in_stream = opts["in_stream"]
        if in_stream is None:
            # If in_stream hasn't been overridden, and we're async, we don't
            # want to read from sys.stdin (otherwise the default) - so set
            # False instead.
            in_stream = False if self._asynchronous else sys.stdin
        # Determine pty or no
        self.using_pty = self.should_use_pty(opts["pty"], opts["fallback"])
        if opts["watchers"]:
            self.watchers = opts["watchers"]
        # Set data
        self.opts = opts
        self.streams = {"out": out_stream, "err": err_stream, "in": in_stream}

    def _collate_result(self, watcher_errors: List[WatcherError]) -> "Result":
        # At this point, we had enough success that we want to be returning or
        # raising detailed info about our execution; so we generate a Result.
        stdout = "".join(self.stdout)
        stderr = "".join(self.stderr)
        if WINDOWS:
            # "Universal newlines" - replace all standard forms of
            # newline with \n. This is not technically Windows related
            # (\r as newline is an old Mac convention) but we only apply
            # the translation for Windows as that's the only platform
            # it is likely to matter for these days.
            stdout = stdout.replace("\r\n", "\n").replace("\r", "\n")
            stderr = stderr.replace("\r\n", "\n").replace("\r", "\n")
        # Get return/exit code, unless there were WatcherErrors to handle.
        # NOTE: In that case, returncode() may block waiting on the process
        # (which may be waiting for user input). Since most WatcherError
        # situations lack a useful exit code anyways, skipping this doesn't
        # really hurt any.
        exited = None if watcher_errors else self.returncode()
        # TODO: as noted elsewhere, I kinda hate this. Consider changing
        # generate_result()'s API in next major rev so we can tidy up.
        result = self.generate_result(
            **dict(
                self.result_kwargs, stdout=stdout, stderr=stderr, exited=exited
            )
        )
        return result

    def _thread_join_timeout(self, target: Callable) -> Optional[int]:
        # Add a timeout to out/err thread joins when it looks like they're not
        # dead but their counterpart is dead; this indicates issue #351 (fixed
        # by #432) where the subproc may hang because its stdout (or stderr) is
        # no longer being consumed by the dead thread (and a pipe is filling
        # up.) In that case, the non-dead thread is likely to block forever on
        # a `recv` unless we add this timeout.
        if target == self.handle_stdin:
            return None
        opposite = self.handle_stderr
        if target == self.handle_stderr:
            opposite = self.handle_stdout
        if opposite in self.threads and self.threads[opposite].is_dead:
            return 1
        return None

    def create_io_threads(
        self,
    ) -> Tuple[Dict[Callable, ExceptionHandlingThread], List[str], List[str]]:
        """
        Create and return a dictionary of IO thread worker objects.

        Caller is expected to handle persisting and/or starting the wrapped
        threads.
        """
        stdout: List[str] = []
        stderr: List[str] = []
        # Set up IO thread parameters (format - body_func: {kwargs})
        thread_args: Dict[Callable, Any] = {
            self.handle_stdout: {
                "buffer_": stdout,
                "hide": "stdout" in self.opts["hide"],
                "output": self.streams["out"],
            }
        }
        # After opt processing above, in_stream will be a real stream obj or
        # False, so we can truth-test it. We don't even create a stdin-handling
        # thread if it's False, meaning user indicated stdin is nonexistent or
        # problematic.
        if self.streams["in"]:
            thread_args[self.handle_stdin] = {
                "input_": self.streams["in"],
                "output": self.streams["out"],
                "echo": self.opts["echo_stdin"],
            }
        if not self.using_pty:
            thread_args[self.handle_stderr] = {
                "buffer_": stderr,
                "hide": "stderr" in self.opts["hide"],
                "output": self.streams["err"],
            }
        # Kick off IO threads
        threads = {}
        for target, kwargs in thread_args.items():
            t = ExceptionHandlingThread(target=target, kwargs=kwargs)
            threads[target] = t
        return threads, stdout, stderr

    def generate_result(self, **kwargs: Any) -> "Result":
        """
        Create & return a suitable `Result` instance from the given ``kwargs``.

        Subclasses may wish to override this in order to manipulate things or
        generate a `Result` subclass (e.g. ones containing additional metadata
        besides the default).

        .. versionadded:: 1.0
        """
        return Result(**kwargs)

    def read_proc_output(self, reader: Callable) -> Generator[str, None, None]:
        """
        Iteratively read & decode bytes from a subprocess' out/err stream.

        :param reader:
            A literal reader function/partial, wrapping the actual stream
            object in question, which takes a number of bytes to read, and
            returns that many bytes (or ``None``).

            ``reader`` should be a reference to either `read_proc_stdout` or
            `read_proc_stderr`, which perform the actual, platform/library
            specific read calls.

        :returns:
            A generator yielding strings.

            Specifically, each resulting string is the result of decoding
            `read_chunk_size` bytes read from the subprocess' out/err stream.

        .. versionadded:: 1.0
        """
        # NOTE: Typically, reading from any stdout/err (local, remote or
        # otherwise) can be thought of as "read until you get nothing back".
        # This is preferable over "wait until an out-of-band signal claims the
        # process is done running" because sometimes that signal will appear
        # before we've actually read all the data in the stream (i.e.: a race
        # condition).
        while True:
            data = reader(self.read_chunk_size)
            if not data:
                break
            yield self.decode(data)

    def write_our_output(self, stream: IO, string: str) -> None:
        """
        Write ``string`` to ``stream``.

        Also calls ``.flush()`` on ``stream`` to ensure that real terminal
        streams don't buffer.

        :param stream:
            A file-like stream object, mapping to the ``out_stream`` or
            ``err_stream`` parameters of `run`.

        :param string: A Unicode string object.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        stream.write(string)
        stream.flush()

    def _handle_output(
        self,
        buffer_: List[str],
        hide: bool,
        output: IO,
        reader: Callable,
    ) -> None:
        # TODO: store un-decoded/raw bytes somewhere as well...
        for data in self.read_proc_output(reader):
            # Echo to local stdout if necessary
            # TODO: should we rephrase this as "if you want to hide, give me a
            # dummy output stream, e.g. something like /dev/null"? Otherwise, a
            # combo of 'hide=stdout' + 'here is an explicit out_stream' means
            # out_stream is never written to, and that seems...odd.
            if not hide:
                self.write_our_output(stream=output, string=data)
            # Store in shared buffer so main thread can do things with the
            # result after execution completes.
            # NOTE: this is threadsafe insofar as no reading occurs until after
            # the thread is join()'d.
            buffer_.append(data)
            # Run our specific buffer through the autoresponder framework
            self.respond(buffer_)

    def handle_stdout(
        self, buffer_: List[str], hide: bool, output: IO
    ) -> None:
        """
        Read process' stdout, storing into a buffer & printing/parsing.

        Intended for use as a thread target. Only terminates when all stdout
        from the subprocess has been read.

        :param buffer_: The capture buffer shared with the main thread.
        :param bool hide: Whether or not to replay data into ``output``.
        :param output:
            Output stream (file-like object) to write data into when not
            hiding.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        self._handle_output(
            buffer_, hide, output, reader=self.read_proc_stdout
        )

    def handle_stderr(
        self, buffer_: List[str], hide: bool, output: IO
    ) -> None:
        """
        Read process' stderr, storing into a buffer & printing/parsing.

        Identical to `handle_stdout` except for the stream read from; see its
        docstring for API details.

        .. versionadded:: 1.0
        """
        self._handle_output(
            buffer_, hide, output, reader=self.read_proc_stderr
        )

    def read_our_stdin(self, input_: IO) -> Optional[str]:
        """
        Read & decode bytes from a local stdin stream.

        :param input_:
            Actual stream object to read from. Maps to ``in_stream`` in `run`,
            so will often be ``sys.stdin``, but might be any stream-like
            object.

        :returns:
            A Unicode string, the result of decoding the read bytes (this might
            be the empty string if the pipe has closed/reached EOF); or
            ``None`` if stdin wasn't ready for reading yet.

        .. versionadded:: 1.0
        """
        # TODO: consider moving the character_buffered contextmanager call in
        # here? Downside is it would be flipping those switches for every byte
        # read instead of once per session, which could be costly (?).
        bytes_ = None
        if ready_for_reading(input_):
            try:
                bytes_ = input_.read(bytes_to_read(input_))
            except OSError as e:
                # Assume EBADF in this situation implies running under nohup or
                # similar, where:
                # - we cannot reliably detect a bad FD up front
                # - trying to read it would explode
                # - user almost surely doesn't care about stdin anyways
                # and ignore it (but not other OSErrors!)
                if e.errno != errno.EBADF:
                    raise
            # Decode if it appears to be binary-type. (From real terminal
            # streams, usually yes; from file-like objects, often no.)
            if bytes_ and isinstance(bytes_, bytes):
                # TODO: will decoding 1 byte at a time break multibyte
                # character encodings? How to square interactivity with that?
                bytes_ = self.decode(bytes_)
        return bytes_

    def handle_stdin(
        self,
        input_: IO,
        output: IO,
        echo: bool = False,
    ) -> None:
        """
        Read local stdin, copying into process' stdin as necessary.

        Intended for use as a thread target.

        .. note::
            Because real terminal stdin streams have no well-defined "end", if
            such a stream is detected (based on existence of a callable
            ``.fileno()``) this method will wait until `program_finished` is
            set, before terminating.

            When the stream doesn't appear to be from a terminal, the same
            semantics as `handle_stdout` are used - the stream is simply
            ``read()`` from until it returns an empty value.

        :param input_: Stream (file-like object) from which to read.
        :param output: Stream (file-like object) to which echoing may occur.
        :param bool echo: User override option for stdin-stdout echoing.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        # TODO: reinstate lock/whatever thread logic from fab v1 which prevents
        # reading from stdin while other parts of the code are prompting for
        # runtime passwords? (search for 'input_enabled')
        # TODO: fabric#1339 is strongly related to this, if it's not literally
        # exposing some regression in Fabric 1.x itself.
        closed_stdin = False
        with character_buffered(input_):
            while True:
                data = self.read_our_stdin(input_)
                if data:
                    # Mirror what we just read to process' stdin.
                    # We encode to ensure bytes, but skip the decode step since
                    # there's presumably no need (nobody's interacting with
                    # this data programmatically).
                    self.write_proc_stdin(data)
                    # Also echo it back to local stdout (or whatever
                    # out_stream is set to) when necessary.
                    if echo is None:
                        echo = self.should_echo_stdin(input_, output)
                    if echo:
                        self.write_our_output(stream=output, string=data)
                # Empty string/char/byte != None. Can't just use 'else' here.
                elif data is not None:
                    # When reading from file-like objects that aren't "real"
                    # terminal streams, an empty byte signals EOF.
                    if not self.using_pty and not closed_stdin:
                        self.close_proc_stdin()
                        closed_stdin = True
                # Dual all-done signals: program being executed is done
                # running, *and* we don't seem to be reading anything out of
                # stdin. (NOTE: If we only test the former, we may encounter
                # race conditions re: unread stdin.)
                if self.program_finished.is_set() and not data:
                    break
                # Take a nap so we're not chewing CPU.
                time.sleep(self.input_sleep)

    def should_echo_stdin(self, input_: IO, output: IO) -> bool:
        """
        Determine whether data read from ``input_`` should echo to ``output``.

        Used by `handle_stdin`; tests attributes of ``input_`` and ``output``.

        :param input_: Input stream (file-like object).
        :param output: Output stream (file-like object).
        :returns: A ``bool``.

        .. versionadded:: 1.0
        """
        return (not self.using_pty) and isatty(input_)

    def respond(self, buffer_: List[str]) -> None:
        """
        Write to the program's stdin in response to patterns in ``buffer_``.

        The patterns and responses are driven by the `.StreamWatcher` instances
        from the ``watchers`` kwarg of `run` - see :doc:`/concepts/watchers`
        for a conceptual overview.

        :param buffer:
            The capture buffer for this thread's particular IO stream.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        # Join buffer contents into a single string; without this,
        # StreamWatcher subclasses can't do things like iteratively scan for
        # pattern matches.
        # NOTE: using string.join should be "efficient enough" for now, re:
        # speed and memory use. Should that become false, consider using
        # StringIO or cStringIO (tho the latter doesn't do Unicode well?) which
        # is apparently even more efficient.
        stream = "".join(buffer_)
        for watcher in self.watchers:
            for response in watcher.submit(stream):
                self.write_proc_stdin(response)

    def generate_env(
        self, env: Dict[str, Any], replace_env: bool
    ) -> Dict[str, Any]:
        """
        Return a suitable environment dict based on user input & behavior.

        :param dict env: Dict supplying overrides or full env, depending.
        :param bool replace_env:
            Whether ``env`` updates, or is used in place of, the value of
            `os.environ`.

        :returns: A dictionary of shell environment vars.

        .. versionadded:: 1.0
        """
        return env if replace_env else dict(os.environ, **env)

    def should_use_pty(self, pty: bool, fallback: bool) -> bool:
        """
        Should execution attempt to use a pseudo-terminal?

        :param bool pty:
            Whether the user explicitly asked for a pty.
        :param bool fallback:
            Whether falling back to non-pty execution should be allowed, in
            situations where ``pty=True`` but a pty could not be allocated.

        .. versionadded:: 1.0
        """
        # NOTE: fallback not used: no falling back implemented by default.
        return pty

    @property
    def has_dead_threads(self) -> bool:
        """
        Detect whether any IO threads appear to have terminated unexpectedly.

        Used during process-completion waiting (in `wait`) to ensure we don't
        deadlock our child process if our IO processing threads have
        errored/died.

        :returns:
            ``True`` if any threads appear to have terminated with an
            exception, ``False`` otherwise.

        .. versionadded:: 1.0
        """
        return any(x.is_dead for x in self.threads.values())

    def wait(self) -> None:
        """
        Block until the running command appears to have exited.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        while True:
            proc_finished = self.process_is_finished
            dead_threads = self.has_dead_threads
            if proc_finished or dead_threads:
                break
            time.sleep(self.input_sleep)

    def write_proc_stdin(self, data: str) -> None:
        """
        Write encoded ``data`` to the running process' stdin.

        :param data: A Unicode string.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        # Encode always, then request implementing subclass to perform the
        # actual write to subprocess' stdin.
        self._write_proc_stdin(data.encode(self.encoding))

    def decode(self, data: bytes) -> str:
        """
        Decode some ``data`` bytes, returning Unicode.

        .. versionadded:: 1.0
        """
        # NOTE: yes, this is a 1-liner. The point is to make it much harder to
        # forget to use 'replace' when decoding :)
        return data.decode(self.encoding, "replace")

    @property
    def process_is_finished(self) -> bool:
        """
        Determine whether our subprocess has terminated.

        .. note::
            The implementation of this method should be nonblocking, as it is
            used within a query/poll loop.

        :returns:
            ``True`` if the subprocess has finished running, ``False``
            otherwise.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def start(self, command: str, shell: str, env: Dict[str, Any]) -> None:
        """
        Initiate execution of ``command`` (via ``shell``, with ``env``).

        Typically this means use of a forked subprocess or requesting start of
        execution on a remote system.

        In most cases, this method will also set subclass-specific member
        variables used in other methods such as `wait` and/or `returncode`.

        :param str command:
            Command string to execute.

        :param str shell:
            Shell to use when executing ``command``.

        :param dict env:
            Environment dict used to prep shell environment.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def start_timer(self, timeout: int) -> None:
        """
        Start a timer to `kill` our subprocess after ``timeout`` seconds.
        """
        if timeout is not None:
            self._timer = threading.Timer(timeout, self.kill)
            self._timer.start()

    def read_proc_stdout(self, num_bytes: int) -> Optional[bytes]:
        """
        Read ``num_bytes`` from the running process' stdout stream.

        :param int num_bytes: Number of bytes to read at maximum.

        :returns: A string/bytes object.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def read_proc_stderr(self, num_bytes: int) -> Optional[bytes]:
        """
        Read ``num_bytes`` from the running process' stderr stream.

        :param int num_bytes: Number of bytes to read at maximum.

        :returns: A string/bytes object.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def _write_proc_stdin(self, data: bytes) -> None:
        """
        Write ``data`` to running process' stdin.

        This should never be called directly; it's for subclasses to implement.
        See `write_proc_stdin` for the public API call.

        :param data: Already-encoded byte data suitable for writing.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def close_proc_stdin(self) -> None:
        """
        Close running process' stdin.

        :returns: ``None``.

        .. versionadded:: 1.3
        """
        raise NotImplementedError

    def default_encoding(self) -> str:
        """
        Return a string naming the expected encoding of subprocess streams.

        This return value should be suitable for use by encode/decode methods.

        .. versionadded:: 1.0
        """
        # TODO: probably wants to be 2 methods, one for local and one for
        # subprocess. For now, good enough to assume both are the same.
        return default_encoding()

    def send_interrupt(self, interrupt: "KeyboardInterrupt") -> None:
        """
        Submit an interrupt signal to the running subprocess.

        In almost all implementations, the default behavior is what will be
        desired: submit ``\x03`` to the subprocess' stdin pipe. However, we
        leave this as a public method in case this default needs to be
        augmented or replaced.

        :param interrupt:
            The locally-sourced ``KeyboardInterrupt`` causing the method call.

        :returns: ``None``.

        .. versionadded:: 1.0
        """
        self.write_proc_stdin("\x03")

    def returncode(self) -> Optional[int]:
        """
        Return the numeric return/exit code resulting from command execution.

        :returns:
            `int`, if any reasonable return code could be determined, or
            ``None`` in corner cases where that was not possible.

        .. versionadded:: 1.0
        """
        raise NotImplementedError

    def stop(self) -> None:
        """
        Perform final cleanup, if necessary.

        This method is called within a ``finally`` clause inside the main `run`
        method. Depending on the subclass, it may be a no-op, or it may do
        things such as close network connections or open files.

        :returns: ``None``

        .. versionadded:: 1.0
        """
        if self._timer:
            self._timer.cancel()

    def kill(self) -> None:
        """
        Forcibly terminate the subprocess.

        Typically only used by the timeout functionality.

        This is often a "best-effort" attempt, e.g. remote subprocesses often
        must settle for simply shutting down the local side of the network
        connection and hoping the remote end eventually gets the message.
        """
        raise NotImplementedError

    @property
    def timed_out(self) -> bool:
        """
        Returns ``True`` if the subprocess stopped because it timed out.

        .. versionadded:: 1.3
        """
        # Timer expiry implies we did time out. (The timer itself will have
        # killed the subprocess, allowing us to even get to this point.)
        return bool(self._timer and not self._timer.is_alive())


class Local(Runner):
    """
    Execute a command on the local system in a subprocess.

    .. note::
        When Invoke itself is executed without a controlling terminal (e.g.
        when ``sys.stdin`` lacks a useful ``fileno``), it's not possible to
        present a handle on our PTY to local subprocesses. In such situations,
        `Local` will fallback to behaving as if ``pty=False`` (on the theory
        that degraded execution is better than none at all) as well as printing
        a warning to stderr.

        To disable this behavior, say ``fallback=False``.

    .. versionadded:: 1.0
    """

    def __init__(self, context: "Context") -> None:
        super().__init__(context)
        # Bookkeeping var for pty use case
        self.status = 0

    def should_use_pty(self, pty: bool = False, fallback: bool = True) -> bool:
        use_pty = False
        if pty:
            use_pty = True
            # TODO: pass in & test in_stream, not sys.stdin
            if not has_fileno(sys.stdin) and fallback:
                if not self.warned_about_pty_fallback:
                    err = "WARNING: stdin has no fileno; falling back to non-pty execution!\n"  # noqa
                    sys.stderr.write(err)
                    self.warned_about_pty_fallback = True
                use_pty = False
        return use_pty

    def read_proc_stdout(self, num_bytes: int) -> Optional[bytes]:
        # Obtain useful read-some-bytes function
        if self.using_pty:
            # Need to handle spurious OSErrors on some Linux platforms.
            try:
                data = os.read(self.parent_fd, num_bytes)
            except OSError as e:
                # Only eat I/O specific OSErrors so we don't hide others
                stringified = str(e)
                io_errors = (
                    # The typical default
                    "Input/output error",
                    # Some less common platforms phrase it this way
                    "I/O error",
                )
                if not any(error in stringified for error in io_errors):
                    raise
                # The bad OSErrors happen after all expected output has
                # appeared, so we return a falsey value, which triggers the
                # "end of output" logic in code using reader functions.
                data = None
        elif self.process and self.process.stdout:
            data = os.read(self.process.stdout.fileno(), num_bytes)
        else:
            data = None
        return data

    def read_proc_stderr(self, num_bytes: int) -> Optional[bytes]:
        # NOTE: when using a pty, this will never be called.
        # TODO: do we ever get those OSErrors on stderr? Feels like we could?
        if self.process and self.process.stderr:
            return os.read(self.process.stderr.fileno(), num_bytes)
        return None

    def _write_proc_stdin(self, data: bytes) -> None:
        # NOTE: parent_fd from os.fork() is a read/write pipe attached to our
        # forked process' stdout/stdin, respectively.
        if self.using_pty:
            fd = self.parent_fd
        elif self.process and self.process.stdin:
            fd = self.process.stdin.fileno()
        else:
            raise SubprocessPipeError(
                "Unable to write to missing subprocess or stdin!"
            )
        # Try to write, ignoring broken pipes if encountered (implies child
        # process exited before the process piping stdin to us finished;
        # there's nothing we can do about that!)
        try:
            os.write(fd, data)
        except OSError as e:
            if "Broken pipe" not in str(e):
                raise

    def close_proc_stdin(self) -> None:
        if self.using_pty:
            # there is no working scenario to tell the process that stdin
            # closed when using pty
            raise SubprocessPipeError("Cannot close stdin when pty=True")
        elif self.process and self.process.stdin:
            self.process.stdin.close()
        else:
            raise SubprocessPipeError(
                "Unable to close missing subprocess or stdin!"
            )

    def start(self, command: str, shell: str, env: Dict[str, Any]) -> None:
        if self.using_pty:
            if pty is None:  # Encountered ImportError
                err = "You indicated pty=True, but your platform doesn't support the 'pty' module!"  # noqa
                sys.exit(err)
            cols, rows = pty_size()
            self.pid, self.parent_fd = pty.fork()
            # If we're the child process, load up the actual command in a
            # shell, just as subprocess does; this replaces our process - whose
            # pipes are all hooked up to the PTY - with the "real" one.
            if self.pid == 0:
                # TODO: both pty.spawn() and pexpect.spawn() do a lot of
                # setup/teardown involving tty.setraw, getrlimit, signal.
                # Ostensibly we'll want some of that eventually, but if
                # possible write tests - integration-level if necessary -
                # before adding it!
                #
                # Set pty window size based on what our own controlling
                # terminal's window size appears to be.
                # TODO: make subroutine?
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(sys.stdout.fileno(), termios.TIOCSWINSZ, winsize)
                # Use execve for bare-minimum "exec w/ variable # args + env"
                # behavior. No need for the 'p' (use PATH to find executable)
                # for now.
                # NOTE: stdlib subprocess (actually its posix flavor, which is
                # written in C) uses either execve or execv, depending.
                os.execve(shell, [shell, "-c", command], env)
        else:
            self.process = Popen(
                command,
                shell=True,
                executable=shell,
                env=env,
                stdout=PIPE,
                stderr=PIPE,
                stdin=PIPE,
            )

    def kill(self) -> None:
        pid = self.pid if self.using_pty else self.process.pid
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            # In odd situations where our subprocess is already dead, don't
            # throw this upwards.
            pass

    @property
    def process_is_finished(self) -> bool:
        if self.using_pty:
            # NOTE:
            # https://github.com/pexpect/ptyprocess/blob/4058faa05e2940662ab6da1330aa0586c6f9cd9c/ptyprocess/ptyprocess.py#L680-L687
            # implies that Linux "requires" use of the blocking, non-WNOHANG
            # version of this call. Our testing doesn't verify this, however,
            # so...
            # NOTE: It does appear to be totally blocking on Windows, so our
            # issue #351 may be totally unsolvable there. Unclear.
            pid_val, self.status = os.waitpid(self.pid, os.WNOHANG)
            return pid_val != 0
        else:
            return self.process.poll() is not None

    def returncode(self) -> Optional[int]:
        if self.using_pty:
            # No subprocess.returncode available; use WIFEXITED/WIFSIGNALED to
            # determine whch of WEXITSTATUS / WTERMSIG to use.
            # TODO: is it safe to just say "call all WEXITSTATUS/WTERMSIG and
            # return whichever one of them is nondefault"? Probably not?
            # NOTE: doing this in an arbitrary order should be safe since only
            # one of the WIF* methods ought to ever return True.
            code = None
            if os.WIFEXITED(self.status):
                code = os.WEXITSTATUS(self.status)
            elif os.WIFSIGNALED(self.status):
                code = os.WTERMSIG(self.status)
                # Match subprocess.returncode by turning signals into negative
                # 'exit code' integers.
                code = -1 * code
            return code
            # TODO: do we care about WIFSTOPPED? Maybe someday?
        else:
            return self.process.returncode

    def stop(self) -> None:
        super().stop()
        # If we opened a PTY for child communications, make sure to close() it,
        # otherwise long-running Invoke-using processes exhaust their file
        # descriptors eventually.
        if self.using_pty:
            try:
                os.close(self.parent_fd)
            except Exception:
                # If something weird happened preventing the close, there's
                # nothing to be done about it now...
                pass


class Result:
    """
    A container for information about the result of a command execution.

    All params are exposed as attributes of the same name and type.

    :param str stdout:
        The subprocess' standard output.

    :param str stderr:
        Same as ``stdout`` but containing standard error (unless the process
        was invoked via a pty, in which case it will be empty; see
        `.Runner.run`.)

    :param str encoding:
        The string encoding used by the local shell environment.

    :param str command:
        The command which was executed.

    :param str shell:
        The shell binary used for execution.

    :param dict env:
        The shell environment used for execution. (Default is the empty dict,
        ``{}``, not ``None`` as displayed in the signature.)

    :param int exited:
        An integer representing the subprocess' exit/return code.

        .. note::
            This may be ``None`` in situations where the subprocess did not run
            to completion, such as when auto-responding failed or a timeout was
            reached.

    :param bool pty:
        A boolean describing whether the subprocess was invoked with a pty or
        not; see `.Runner.run`.

    :param tuple hide:
        A tuple of stream names (none, one or both of ``('stdout', 'stderr')``)
        which were hidden from the user when the generating command executed;
        this is a normalized value derived from the ``hide`` parameter of
        `.Runner.run`.

        For example, ``run('command', hide='stdout')`` will yield a `Result`
        where ``result.hide == ('stdout',)``; ``hide=True`` or ``hide='both'``
        results in ``result.hide == ('stdout', 'stderr')``; and ``hide=False``
        (the default) generates ``result.hide == ()`` (the empty tuple.)

    .. note::
        `Result` objects' truth evaluation is equivalent to their `.ok`
        attribute's value. Therefore, quick-and-dirty expressions like the
        following are possible::

            if run("some shell command"):
                do_something()
            else:
                handle_problem()

        However, remember `Zen of Python #2
        <http://zen-of-python.info/explicit-is-better-than-implicit.html#2>`_.

    .. versionadded:: 1.0
    """

    # TODO: inherit from namedtuple instead? heh (or: use attrs from pypi)
    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        encoding: Optional[str] = None,
        command: str = "",
        shell: str = "",
        env: Optional[Dict[str, Any]] = None,
        exited: int = 0,
        pty: bool = False,
        hide: Tuple[str, ...] = tuple(),
    ):
        self.stdout = stdout
        self.stderr = stderr
        if encoding is None:
            encoding = default_encoding()
        self.encoding = encoding
        self.command = command
        self.shell = shell
        self.env = {} if env is None else env
        self.exited = exited
        self.pty = pty
        self.hide = hide

    @property
    def return_code(self) -> int:
        """
        An alias for ``.exited``.

        .. versionadded:: 1.0
        """
        return self.exited

    def __bool__(self) -> bool:
        return self.ok

    def __str__(self) -> str:
        if self.exited is not None:
            desc = "Command exited with status {}.".format(self.exited)
        else:
            desc = "Command was not fully executed due to watcher error."
        ret = [desc]
        for x in ("stdout", "stderr"):
            val = getattr(self, x)
            ret.append(
                """=== {} ===
{}
""".format(
                    x, val.rstrip()
                )
                if val
                else "(no {})".format(x)
            )
        return "\n".join(ret)

    def __repr__(self) -> str:
        # TODO: more? e.g. len of stdout/err? (how to represent cleanly in a
        # 'x=y' format like this? e.g. '4b' is ambiguous as to what it
        # represents
        template = "<Result cmd={!r} exited={}>"
        return template.format(self.command, self.exited)

    @property
    def ok(self) -> bool:
        """
        A boolean equivalent to ``exited == 0``.

        .. versionadded:: 1.0
        """
        return bool(self.exited == 0)

    @property
    def failed(self) -> bool:
        """
        The inverse of ``ok``.

        I.e., ``True`` if the program exited with a nonzero return code, and
        ``False`` otherwise.

        .. versionadded:: 1.0
        """
        return not self.ok

    def tail(self, stream: str, count: int = 10) -> str:
        """
        Return the last ``count`` lines of ``stream``, plus leading whitespace.

        :param str stream:
            Name of some captured stream attribute, eg ``"stdout"``.
        :param int count:
            Number of lines to preserve.

        .. versionadded:: 1.3
        """
        # TODO: preserve alternate line endings? Mehhhh
        # NOTE: no trailing \n preservation; easier for below display if
        # normalized
        return "\n\n" + "\n".join(getattr(self, stream).splitlines()[-count:])


class Promise(Result):
    """
    A promise of some future `Result`, yielded from asynchronous execution.

    This class' primary API member is `join`; instances may also be used as
    context managers, which will automatically call `join` when the block
    exits. In such cases, the context manager yields ``self``.

    `Promise` also exposes copies of many `Result` attributes, specifically
    those that derive from `~Runner.run` kwargs and not the result of command
    execution. For example, ``command`` is replicated here, but ``stdout`` is
    not.

    .. versionadded:: 1.4
    """

    def __init__(self, runner: "Runner") -> None:
        """
        Create a new promise.

        :param runner:
            An in-flight `Runner` instance making this promise.

            Must already have started the subprocess and spun up IO threads.
        """
        self.runner = runner
        # Basically just want exactly this (recently refactored) kwargs dict.
        # TODO: consider proxying vs copying, but prob wait for refactor
        for key, value in self.runner.result_kwargs.items():
            setattr(self, key, value)

    def join(self) -> Result:
        """
        Block until associated subprocess exits, returning/raising the result.

        This acts identically to the end of a synchronously executed ``run``,
        namely that:

        - various background threads (such as IO workers) are themselves
          joined;
        - if the subprocess exited normally, a `Result` is returned;
        - in any other case (unforeseen exceptions, IO sub-thread
          `.ThreadException`, `.Failure`, `.WatcherError`) the relevant
          exception is raised here.

        See `~Runner.run` docs, or those of the relevant classes, for further
        details.
        """
        try:
            return self.runner._finish()
        finally:
            self.runner.stop()

    def __enter__(self) -> "Promise":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: BaseException,
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.join()


def normalize_hide(
    val: Any,
    out_stream: Optional[str] = None,
    err_stream: Optional[str] = None,
) -> Tuple[str, ...]:
    # Normalize to list-of-stream-names
    hide_vals = (None, False, "out", "stdout", "err", "stderr", "both", True)
    if val not in hide_vals:
        err = "'hide' got {!r} which is not in {!r}"
        raise ValueError(err.format(val, hide_vals))
    if val in (None, False):
        hide = []
    elif val in ("both", True):
        hide = ["stdout", "stderr"]
    elif val == "out":
        hide = ["stdout"]
    elif val == "err":
        hide = ["stderr"]
    else:
        hide = [val]
    # Revert any streams that have been overridden from the default value
    if out_stream is not None and "stdout" in hide:
        hide.remove("stdout")
    if err_stream is not None and "stderr" in hide:
        hide.remove("stderr")
    return tuple(hide)


def default_encoding() -> str:
    """
    Obtain apparent interpreter-local default text encoding.

    Often used as a baseline in situations where we must use SOME encoding for
    unknown-but-presumably-text bytes, and the user has not specified an
    override.
    """
    encoding = locale.getpreferredencoding(False)
    return encoding
