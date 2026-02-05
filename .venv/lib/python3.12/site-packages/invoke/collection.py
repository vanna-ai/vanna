import copy
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple

from .util import Lexicon, helpline

from .config import merge_dicts, copy_dict
from .parser import Context as ParserContext
from .tasks import Task


class Collection:
    """
    A collection of executable tasks. See :doc:`/concepts/namespaces`.

    .. versionadded:: 1.0
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Create a new task collection/namespace.

        `.Collection` offers a set of methods for building a collection of
        tasks from scratch, plus a convenient constructor wrapping said API.

        In either case:

        * The first positional argument may be a string, which (if given) is
          used as the collection's default name when performing namespace
          lookups;
        * A ``loaded_from`` keyword argument may be given, which sets metadata
          indicating the filesystem path the collection was loaded from. This
          is used as a guide when loading per-project :ref:`configuration files
          <config-hierarchy>`.
        * An ``auto_dash_names`` kwarg may be given, controlling whether task
          and collection names have underscores turned to dashes in most cases;
          it defaults to ``True`` but may be set to ``False`` to disable.

          The CLI machinery will pass in the value of the
          ``tasks.auto_dash_names`` config value to this kwarg.

        **The method approach**

        May initialize with no arguments and use methods (e.g.
        `.add_task`/`.add_collection`) to insert objects::

            c = Collection()
            c.add_task(some_task)

        If an initial string argument is given, it is used as the default name
        for this collection, should it be inserted into another collection as a
        sub-namespace::

            docs = Collection('docs')
            docs.add_task(doc_task)
            ns = Collection()
            ns.add_task(top_level_task)
            ns.add_collection(docs)
            # Valid identifiers are now 'top_level_task' and 'docs.doc_task'
            # (assuming the task objects were actually named the same as the
            # variables we're using :))

        For details, see the API docs for the rest of the class.

        **The constructor approach**

        All ``*args`` given to `.Collection` (besides the abovementioned
        optional positional 'name' argument and ``loaded_from`` kwarg) are
        expected to be `.Task` or `.Collection` instances which will be passed
        to `.add_task`/`.add_collection` as appropriate. Module objects are
        also valid (as they are for `.add_collection`). For example, the below
        snippet results in the same two task identifiers as the one above::

            ns = Collection(top_level_task, Collection('docs', doc_task))

        If any ``**kwargs`` are given, the keywords are used as the initial
        name arguments for the respective values::

            ns = Collection(
                top_level_task=some_other_task,
                docs=Collection(doc_task)
            )

        That's exactly equivalent to::

            docs = Collection(doc_task)
            ns = Collection()
            ns.add_task(some_other_task, 'top_level_task')
            ns.add_collection(docs, 'docs')

        See individual methods' API docs for details.
        """
        # Initialize
        self.tasks = Lexicon()
        self.collections = Lexicon()
        self.default: Optional[str] = None
        self.name = None
        self._configuration: Dict[str, Any] = {}
        # Specific kwargs if applicable
        self.loaded_from = kwargs.pop("loaded_from", None)
        self.auto_dash_names = kwargs.pop("auto_dash_names", None)
        # splat-kwargs version of default value (auto_dash_names=True)
        if self.auto_dash_names is None:
            self.auto_dash_names = True
        # Name if applicable
        _args = list(args)
        if _args and isinstance(args[0], str):
            self.name = self.transform(_args.pop(0))
        # Dispatch args/kwargs
        for arg in _args:
            self._add_object(arg)
        # Dispatch kwargs
        for name, obj in kwargs.items():
            self._add_object(obj, name)

    def _add_object(self, obj: Any, name: Optional[str] = None) -> None:
        method: Callable
        if isinstance(obj, Task):
            method = self.add_task
        elif isinstance(obj, (Collection, ModuleType)):
            method = self.add_collection
        else:
            raise TypeError("No idea how to insert {!r}!".format(type(obj)))
        method(obj, name=name)

    def __repr__(self) -> str:
        task_names = list(self.tasks.keys())
        collections = ["{}...".format(x) for x in self.collections.keys()]
        return "<Collection {!r}: {}>".format(
            self.name, ", ".join(sorted(task_names) + sorted(collections))
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Collection):
            return (
                self.name == other.name
                and self.tasks == other.tasks
                and self.collections == other.collections
            )
        return False

    def __bool__(self) -> bool:
        return bool(self.task_names)

    @classmethod
    def from_module(
        cls,
        module: ModuleType,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        loaded_from: Optional[str] = None,
        auto_dash_names: Optional[bool] = None,
    ) -> "Collection":
        """
        Return a new `.Collection` created from ``module``.

        Inspects ``module`` for any `.Task` instances and adds them to a new
        `.Collection`, returning it. If any explicit namespace collections
        exist (named ``ns`` or ``namespace``) a copy of that collection object
        is preferentially loaded instead.

        When the implicit/default collection is generated, it will be named
        after the module's ``__name__`` attribute, or its last dotted section
        if it's a submodule. (I.e. it should usually map to the actual ``.py``
        filename.)

        Explicitly given collections will only be given that module-derived
        name if they don't already have a valid ``.name`` attribute.

        If the module has a docstring (``__doc__``) it is copied onto the
        resulting `.Collection` (and used for display in help, list etc
        output.)

        :param str name:
            A string, which if given will override any automatically derived
            collection name (or name set on the module's root namespace, if it
            has one.)

        :param dict config:
            Used to set config options on the newly created `.Collection`
            before returning it (saving you a call to `.configure`.)

            If the imported module had a root namespace object, ``config`` is
            merged on top of it (i.e. overriding any conflicts.)

        :param str loaded_from:
            Identical to the same-named kwarg from the regular class
            constructor - should be the path where the module was
            found.

        :param bool auto_dash_names:
            Identical to the same-named kwarg from the regular class
            constructor - determines whether emitted names are auto-dashed.

        .. versionadded:: 1.0
        """
        module_name = module.__name__.split(".")[-1]

        def instantiate(obj_name: Optional[str] = None) -> "Collection":
            # Explicitly given name wins over root ns name (if applicable),
            # which wins over actual module name.
            args = [name or obj_name or module_name]
            kwargs = dict(
                loaded_from=loaded_from, auto_dash_names=auto_dash_names
            )
            instance = cls(*args, **kwargs)
            instance.__doc__ = module.__doc__
            return instance

        # See if the module provides a default NS to use in lieu of creating
        # our own collection.
        for candidate in ("ns", "namespace"):
            obj = getattr(module, candidate, None)
            if obj and isinstance(obj, Collection):
                # TODO: make this into Collection.clone() or similar?
                ret = instantiate(obj_name=obj.name)
                ret.tasks = ret._transform_lexicon(obj.tasks)
                ret.collections = ret._transform_lexicon(obj.collections)
                ret.default = (
                    ret.transform(obj.default) if obj.default else None
                )
                # Explicitly given config wins over root ns config
                obj_config = copy_dict(obj._configuration)
                if config:
                    merge_dicts(obj_config, config)
                ret._configuration = obj_config
                return ret
        # Failing that, make our own collection from the module's tasks.
        tasks = filter(lambda x: isinstance(x, Task), vars(module).values())
        # Again, explicit name wins over implicit one from module path
        collection = instantiate()
        for task in tasks:
            collection.add_task(task)
        if config:
            collection.configure(config)
        return collection

    def add_task(
        self,
        task: "Task",
        name: Optional[str] = None,
        aliases: Optional[Tuple[str, ...]] = None,
        default: Optional[bool] = None,
    ) -> None:
        """
        Add `.Task` ``task`` to this collection.

        :param task: The `.Task` object to add to this collection.

        :param name:
            Optional string name to bind to (overrides the task's own
            self-defined ``name`` attribute and/or any Python identifier (i.e.
            ``.func_name``.)

        :param aliases:
            Optional iterable of additional names to bind the task as, on top
            of the primary name. These will be used in addition to any aliases
            the task itself declares internally.

        :param default: Whether this task should be the collection default.

        .. versionadded:: 1.0
        """
        if name is None:
            if task.name:
                name = task.name
            # XXX https://github.com/python/mypy/issues/1424
            elif hasattr(task.body, "func_name"):
                name = task.body.func_name  # type: ignore
            elif hasattr(task.body, "__name__"):
                name = task.__name__
            else:
                raise ValueError("Could not obtain a name for this task!")
        name = self.transform(name)
        if name in self.collections:
            err = "Name conflict: this collection has a sub-collection named {!r} already"  # noqa
            raise ValueError(err.format(name))
        self.tasks[name] = task
        for alias in list(task.aliases) + list(aliases or []):
            self.tasks.alias(self.transform(alias), to=name)
        if default is True or (default is None and task.is_default):
            self._check_default_collision(name)
            self.default = name

    def add_collection(
        self,
        coll: "Collection",
        name: Optional[str] = None,
        default: Optional[bool] = None,
    ) -> None:
        """
        Add `.Collection` ``coll`` as a sub-collection of this one.

        :param coll: The `.Collection` to add.

        :param str name:
            The name to attach the collection as. Defaults to the collection's
            own internal name.

        :param default:
            Whether this sub-collection('s default task-or-collection) should
            be the default invocation of the parent collection.

        .. versionadded:: 1.0
        .. versionchanged:: 1.5
            Added the ``default`` parameter.
        """
        # Handle module-as-collection
        if isinstance(coll, ModuleType):
            coll = Collection.from_module(coll)
        # Ensure we have a name, or die trying
        name = name or coll.name
        if not name:
            raise ValueError("Non-root collections must have a name!")
        name = self.transform(name)
        # Test for conflict
        if name in self.tasks:
            err = "Name conflict: this collection has a task named {!r} already"  # noqa
            raise ValueError(err.format(name))
        # Insert
        self.collections[name] = coll
        if default:
            self._check_default_collision(name)
            self.default = name

    def _check_default_collision(self, name: str) -> None:
        if self.default:
            msg = "'{}' cannot be the default because '{}' already is!"
            raise ValueError(msg.format(name, self.default))

    def _split_path(self, path: str) -> Tuple[str, str]:
        """
        Obtain first collection + remainder, of a task path.

        E.g. for ``"subcollection.taskname"``, return ``("subcollection",
        "taskname")``; for ``"subcollection.nested.taskname"`` return
        ``("subcollection", "nested.taskname")``, etc.

        An empty path becomes simply ``('', '')``.
        """
        parts = path.split(".")
        coll = parts.pop(0)
        rest = ".".join(parts)
        return coll, rest

    def subcollection_from_path(self, path: str) -> "Collection":
        """
        Given a ``path`` to a subcollection, return that subcollection.

        .. versionadded:: 1.0
        """
        parts = path.split(".")
        collection = self
        while parts:
            collection = collection.collections[parts.pop(0)]
        return collection

    def __getitem__(self, name: Optional[str] = None) -> Any:
        """
        Returns task named ``name``. Honors aliases and subcollections.

        If this collection has a default task, it is returned when ``name`` is
        empty or ``None``. If empty input is given and no task has been
        selected as the default, ValueError will be raised.

        Tasks within subcollections should be given in dotted form, e.g.
        'foo.bar'. Subcollection default tasks will be returned on the
        subcollection's name.

        .. versionadded:: 1.0
        """
        return self.task_with_config(name)[0]

    def _task_with_merged_config(
        self, coll: str, rest: str, ours: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        task, config = self.collections[coll].task_with_config(rest)
        return task, dict(config, **ours)

    def task_with_config(
        self, name: Optional[str]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Return task named ``name`` plus its configuration dict.

        E.g. in a deeply nested tree, this method returns the `.Task`, and a
        configuration dict created by merging that of this `.Collection` and
        any nested `Collections <.Collection>`, up through the one actually
        holding the `.Task`.

        See `~.Collection.__getitem__` for semantics of the ``name`` argument.

        :returns: Two-tuple of (`.Task`, `dict`).

        .. versionadded:: 1.0
        """
        # Our top level configuration
        ours = self.configuration()
        # Default task for this collection itself
        if not name:
            if not self.default:
                raise ValueError("This collection has no default task.")
            return self[self.default], ours
        # Normalize name to the format we're expecting
        name = self.transform(name)
        # Non-default tasks within subcollections -> recurse (sorta)
        if "." in name:
            coll, rest = self._split_path(name)
            return self._task_with_merged_config(coll, rest, ours)
        # Default task for subcollections (via empty-name lookup)
        if name in self.collections:
            return self._task_with_merged_config(name, "", ours)
        # Regular task lookup
        return self.tasks[name], ours

    def __contains__(self, name: str) -> bool:
        try:
            self[name]
            return True
        except KeyError:
            return False

    def to_contexts(
        self, ignore_unknown_help: Optional[bool] = None
    ) -> List[ParserContext]:
        """
        Returns all contained tasks and subtasks as a list of parser contexts.

        :param bool ignore_unknown_help:
            Passed on to each task's ``get_arguments()`` method. See the config
            option by the same name for details.

        .. versionadded:: 1.0
        .. versionchanged:: 1.7
            Added the ``ignore_unknown_help`` kwarg.
        """
        result = []
        for primary, aliases in self.task_names.items():
            task = self[primary]
            result.append(
                ParserContext(
                    name=primary,
                    aliases=aliases,
                    args=task.get_arguments(
                        ignore_unknown_help=ignore_unknown_help
                    ),
                )
            )
        return result

    def subtask_name(self, collection_name: str, task_name: str) -> str:
        return ".".join(
            [self.transform(collection_name), self.transform(task_name)]
        )

    def transform(self, name: str) -> str:
        """
        Transform ``name`` with the configured auto-dashes behavior.

        If the collection's ``auto_dash_names`` attribute is ``True``
        (default), all non leading/trailing underscores are turned into dashes.
        (Leading/trailing underscores tend to get stripped elsewhere in the
        stack.)

        If it is ``False``, the inverse is applied - all dashes are turned into
        underscores.

        .. versionadded:: 1.0
        """
        # Short-circuit on anything non-applicable, e.g. empty strings, bools,
        # None, etc.
        if not name:
            return name
        from_, to = "_", "-"
        if not self.auto_dash_names:
            from_, to = "-", "_"
        replaced = []
        end = len(name) - 1
        for i, char in enumerate(name):
            # Don't replace leading or trailing underscores (+ taking dotted
            # names into account)
            # TODO: not 100% convinced of this / it may be exposing a
            # discrepancy between this level & higher levels which tend to
            # strip out leading/trailing underscores entirely.
            if (
                i not in (0, end)
                and char == from_
                and name[i - 1] != "."
                and name[i + 1] != "."
            ):
                char = to
            replaced.append(char)
        return "".join(replaced)

    def _transform_lexicon(self, old: Lexicon) -> Lexicon:
        """
        Take a Lexicon and apply `.transform` to its keys and aliases.

        :returns: A new Lexicon.
        """
        new = Lexicon()
        # Lexicons exhibit only their real keys in most places, so this will
        # only grab those, not aliases.
        for key, value in old.items():
            # Deepcopy the value so we're not just copying a reference
            new[self.transform(key)] = copy.deepcopy(value)
        # Also copy all aliases, which are string-to-string key mappings
        for key, value in old.aliases.items():
            new.alias(from_=self.transform(key), to=self.transform(value))
        return new

    @property
    def task_names(self) -> Dict[str, List[str]]:
        """
        Return all task identifiers for this collection as a one-level dict.

        Specifically, a dict with the primary/"real" task names as the key, and
        any aliases as a list value.

        It basically collapses the namespace tree into a single
        easily-scannable collection of invocation strings, and is thus suitable
        for things like flat-style task listings or transformation into parser
        contexts.

        .. versionadded:: 1.0
        """
        ret = {}
        # Our own tasks get no prefix, just go in as-is: {name: [aliases]}
        for name, task in self.tasks.items():
            ret[name] = list(map(self.transform, task.aliases))
        # Subcollection tasks get both name + aliases prefixed
        for coll_name, coll in self.collections.items():
            for task_name, aliases in coll.task_names.items():
                aliases = list(
                    map(lambda x: self.subtask_name(coll_name, x), aliases)
                )
                # Tack on collection name to alias list if this task is the
                # collection's default.
                if coll.default == task_name:
                    aliases += (coll_name,)
                ret[self.subtask_name(coll_name, task_name)] = aliases
        return ret

    def configuration(self, taskpath: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtain merged configuration values from collection & children.

        :param taskpath:
            (Optional) Task name/path, identical to that used for
            `~.Collection.__getitem__` (e.g. may be dotted for nested tasks,
            etc.) Used to decide which path to follow in the collection tree
            when merging config values.

        :returns: A `dict` containing configuration values.

        .. versionadded:: 1.0
        """
        if taskpath is None:
            return copy_dict(self._configuration)
        return self.task_with_config(taskpath)[1]

    def configure(self, options: Dict[str, Any]) -> None:
        """
        (Recursively) merge ``options`` into the current `.configuration`.

        Options configured this way will be available to all tasks. It is
        recommended to use unique keys to avoid potential clashes with other
        config options

        For example, if you were configuring a Sphinx docs build target
        directory, it's better to use a key like ``'sphinx.target'`` than
        simply ``'target'``.

        :param options: An object implementing the dictionary protocol.
        :returns: ``None``.

        .. versionadded:: 1.0
        """
        merge_dicts(self._configuration, options)

    def serialized(self) -> Dict[str, Any]:
        """
        Return an appropriate-for-serialization version of this object.

        See the documentation for `.Program` and its ``json`` task listing
        format; this method is the driver for that functionality.

        .. versionadded:: 1.0
        """
        return {
            "name": self.name,
            "help": helpline(self),
            "default": self.default,
            "tasks": [
                {
                    "name": self.transform(x.name),
                    "help": helpline(x),
                    "aliases": [self.transform(y) for y in x.aliases],
                }
                for x in sorted(self.tasks.values(), key=lambda x: x.name)
            ],
            "collections": [
                x.serialized()
                for x in sorted(
                    self.collections.values(), key=lambda x: x.name or ""
                )
            ],
        }
