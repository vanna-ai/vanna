"""
Custom exception classes.

These vary in use case from "we needed a specific data structure layout in
exceptions used for message-passing" to simply "we needed to express an error
condition in a way easily told apart from other, truly unexpected errors".
"""

from pprint import pformat
from traceback import format_exception
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .parser import ParserContext
    from .runners import Result
    from .util import ExceptionWrapper


class CollectionNotFound(Exception):
    def __init__(self, name: str, start: str) -> None:
        self.name = name
        self.start = start


class Failure(Exception):
    """
    Exception subclass representing failure of a command execution.

    "Failure" may mean the command executed and the shell indicated an unusual
    result (usually, a non-zero exit code), or it may mean something else, like
    a ``sudo`` command which was aborted when the supplied password failed
    authentication.

    Two attributes allow introspection to determine the nature of the problem:

    * ``result``: a `.Result` instance with info about the command being
      executed and, if it ran to completion, how it exited.
    * ``reason``: a wrapped exception instance if applicable (e.g. a
      `.StreamWatcher` raised `WatcherError`) or ``None`` otherwise, in which
      case, it's probably a `Failure` subclass indicating its own specific
      nature, such as `UnexpectedExit` or `CommandTimedOut`.

    This class is only rarely raised by itself; most of the time `.Runner.run`
    (or a wrapper of same, such as `.Context.sudo`) will raise a specific
    subclass like `UnexpectedExit` or `AuthFailure`.

    .. versionadded:: 1.0
    """

    def __init__(
        self, result: "Result", reason: Optional["WatcherError"] = None
    ) -> None:
        self.result = result
        self.reason = reason

    def streams_for_display(self) -> Tuple[str, str]:
        """
        Return stdout/err streams as necessary for error display.

        Subject to the following rules:

        - If a given stream was *not* hidden during execution, a placeholder is
          used instead, to avoid printing it twice.
        - Only the last 10 lines of stream text is included.
        - PTY-driven execution will lack stderr, and a specific message to this
          effect is returned instead of a stderr dump.

        :returns: Two-tuple of stdout, stderr strings.

        .. versionadded:: 1.3
        """
        already_printed = " already printed"
        if "stdout" not in self.result.hide:
            stdout = already_printed
        else:
            stdout = self.result.tail("stdout")
        if self.result.pty:
            stderr = " n/a (PTYs have no stderr)"
        else:
            if "stderr" not in self.result.hide:
                stderr = already_printed
            else:
                stderr = self.result.tail("stderr")
        return stdout, stderr

    def __repr__(self) -> str:
        return self._repr()

    def _repr(self, **kwargs: Any) -> str:
        """
        Return ``__repr__``-like value from inner result + any kwargs.
        """
        # TODO: expand?
        # TODO: truncate command?
        template = "<{}: cmd={!r}{}>"
        rest = ""
        if kwargs:
            rest = " " + " ".join(
                "{}={}".format(key, value) for key, value in kwargs.items()
            )
        return template.format(
            self.__class__.__name__, self.result.command, rest
        )


class UnexpectedExit(Failure):
    """
    A shell command ran to completion but exited with an unexpected exit code.

    Its string representation displays the following:

    - Command executed;
    - Exit code;
    - The last 10 lines of stdout, if it was hidden;
    - The last 10 lines of stderr, if it was hidden and non-empty (e.g.
      pty=False; when pty=True, stderr never happens.)

    .. versionadded:: 1.0
    """

    def __str__(self) -> str:
        stdout, stderr = self.streams_for_display()
        command = self.result.command
        exited = self.result.exited
        template = """Encountered a bad command exit code!

Command: {!r}

Exit code: {}

Stdout:{}

Stderr:{}

"""
        return template.format(command, exited, stdout, stderr)

    def _repr(self, **kwargs: Any) -> str:
        kwargs.setdefault("exited", self.result.exited)
        return super()._repr(**kwargs)


class CommandTimedOut(Failure):
    """
    Raised when a subprocess did not exit within a desired timeframe.
    """

    def __init__(self, result: "Result", timeout: int) -> None:
        super().__init__(result)
        self.timeout = timeout

    def __repr__(self) -> str:
        return self._repr(timeout=self.timeout)

    def __str__(self) -> str:
        stdout, stderr = self.streams_for_display()
        command = self.result.command
        template = """Command did not complete within {} seconds!

Command: {!r}

Stdout:{}

Stderr:{}

"""
        return template.format(self.timeout, command, stdout, stderr)


class AuthFailure(Failure):
    """
    An authentication failure, e.g. due to an incorrect ``sudo`` password.

    .. note::
        `.Result` objects attached to these exceptions typically lack exit code
        information, since the command was never fully executed - the exception
        was raised instead.

    .. versionadded:: 1.0
    """

    def __init__(self, result: "Result", prompt: str) -> None:
        self.result = result
        self.prompt = prompt

    def __str__(self) -> str:
        err = "The password submitted to prompt {!r} was rejected."
        return err.format(self.prompt)


class ParseError(Exception):
    """
    An error arising from the parsing of command-line flags/arguments.

    Ambiguous input, invalid task names, invalid flags, etc.

    .. versionadded:: 1.0
    """

    def __init__(
        self, msg: str, context: Optional["ParserContext"] = None
    ) -> None:
        super().__init__(msg)
        self.context = context


class Exit(Exception):
    """
    Simple custom stand-in for SystemExit.

    Replaces scattered sys.exit calls, improves testability, allows one to
    catch an exit request without intercepting real SystemExits (typically an
    unfriendly thing to do, as most users calling `sys.exit` rather expect it
    to truly exit.)

    Defaults to a non-printing, exit-0 friendly termination behavior if the
    exception is uncaught.

    If ``code`` (an int) given, that code is used to exit.

    If ``message`` (a string) given, it is printed to standard error, and the
    program exits with code ``1`` by default (unless overridden by also giving
    ``code`` explicitly.)

    .. versionadded:: 1.0
    """

    def __init__(
        self, message: Optional[str] = None, code: Optional[int] = None
    ) -> None:
        self.message = message
        self._code = code

    @property
    def code(self) -> int:
        if self._code is not None:
            return self._code
        return 1 if self.message else 0


class PlatformError(Exception):
    """
    Raised when an illegal operation occurs for the current platform.

    E.g. Windows users trying to use functionality requiring the ``pty``
    module.

    Typically used to present a clearer error message to the user.

    .. versionadded:: 1.0
    """

    pass


class AmbiguousEnvVar(Exception):
    """
    Raised when loading env var config keys has an ambiguous target.

    .. versionadded:: 1.0
    """

    pass


class UncastableEnvVar(Exception):
    """
    Raised on attempted env var loads whose default values are too rich.

    E.g. trying to stuff ``MY_VAR="foo"`` into ``{'my_var': ['uh', 'oh']}``
    doesn't make any sense until/if we implement some sort of transform option.

    .. versionadded:: 1.0
    """

    pass


class UnknownFileType(Exception):
    """
    A config file of an unknown type was specified and cannot be loaded.

    .. versionadded:: 1.0
    """

    pass


class UnpicklableConfigMember(Exception):
    """
    A config file contained module objects, which can't be pickled/copied.

    We raise this more easily catchable exception instead of letting the
    (unclearly phrased) TypeError bubble out of the pickle module. (However, to
    avoid our own fragile catching of that error, we head it off by explicitly
    testing for module members.)

    .. versionadded:: 1.0.2
    """

    pass


def _printable_kwargs(kwargs: Any) -> Dict[str, Any]:
    """
    Return print-friendly version of a thread-related ``kwargs`` dict.

    Extra care is taken with ``args`` members which are very long iterables -
    those need truncating to be useful.
    """
    printable = {}
    for key, value in kwargs.items():
        item = value
        if key == "args":
            item = []
            for arg in value:
                new_arg = arg
                if hasattr(arg, "__len__") and len(arg) > 10:
                    msg = "<... remainder truncated during error display ...>"
                    new_arg = arg[:10] + [msg]
                item.append(new_arg)
        printable[key] = item
    return printable


class ThreadException(Exception):
    """
    One or more exceptions were raised within background threads.

    The real underlying exceptions are stored in the `exceptions` attribute;
    see its documentation for data structure details.

    .. note::
        Threads which did not encounter an exception, do not contribute to this
        exception object and thus are not present inside `exceptions`.

    .. versionadded:: 1.0
    """

    #: A tuple of `ExceptionWrappers <invoke.util.ExceptionWrapper>` containing
    #: the initial thread constructor kwargs (because `threading.Thread`
    #: subclasses should always be called with kwargs) and the caught exception
    #: for that thread as seen by `sys.exc_info` (so: type, value, traceback).
    #:
    #: .. note::
    #:     The ordering of this attribute is not well-defined.
    #:
    #: .. note::
    #:     Thread kwargs which appear to be very long (e.g. IO
    #:     buffers) will be truncated when printed, to avoid huge
    #:     unreadable error display.
    exceptions: Tuple["ExceptionWrapper", ...] = tuple()

    def __init__(self, exceptions: List["ExceptionWrapper"]) -> None:
        self.exceptions = tuple(exceptions)

    def __str__(self) -> str:
        details = []
        for x in self.exceptions:
            # Build useful display
            detail = "Thread args: {}\n\n{}"
            details.append(
                detail.format(
                    pformat(_printable_kwargs(x.kwargs)),
                    "\n".join(format_exception(x.type, x.value, x.traceback)),
                )
            )
        args = (
            len(self.exceptions),
            ", ".join(x.type.__name__ for x in self.exceptions),
            "\n\n".join(details),
        )
        return """
Saw {} exceptions within threads ({}):


{}
""".format(
            *args
        )


class WatcherError(Exception):
    """
    Generic parent exception class for `.StreamWatcher`-related errors.

    Typically, one of these exceptions indicates a `.StreamWatcher` noticed
    something anomalous in an output stream, such as an authentication response
    failure.

    `.Runner` catches these and attaches them to `.Failure` exceptions so they
    can be referenced by intermediate code and/or act as extra info for end
    users.

    .. versionadded:: 1.0
    """

    pass


class ResponseNotAccepted(WatcherError):
    """
    A responder/watcher class noticed a 'bad' response to its submission.

    Mostly used by `.FailingResponder` and subclasses, e.g. "oh dear I
    autosubmitted a sudo password and it was incorrect."

    .. versionadded:: 1.0
    """

    pass


class SubprocessPipeError(Exception):
    """
    Some problem was encountered handling subprocess pipes (stdout/err/in).

    Typically only for corner cases; most of the time, errors in this area are
    raised by the interpreter or the operating system, and end up wrapped in a
    `.ThreadException`.

    .. versionadded:: 1.3
    """

    pass
