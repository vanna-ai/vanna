from typing import Any, Iterable, Optional, Tuple

# TODO: dynamic type for kind
# T = TypeVar('T')


class Argument:
    """
    A command-line argument/flag.

    :param name:
        Syntactic sugar for ``names=[<name>]``. Giving both ``name`` and
        ``names`` is invalid.
    :param names:
        List of valid identifiers for this argument. For example, a "help"
        argument may be defined with a name list of ``['-h', '--help']``.
    :param kind:
        Type factory & parser hint. E.g. ``int`` will turn the default text
        value parsed, into a Python integer; and ``bool`` will tell the
        parser not to expect an actual value but to treat the argument as a
        toggle/flag.
    :param default:
        Default value made available to the parser if no value is given on the
        command line.
    :param help:
        Help text, intended for use with ``--help``.
    :param positional:
        Whether or not this argument's value may be given positionally. When
        ``False`` (default) arguments must be explicitly named.
    :param optional:
        Whether or not this (non-``bool``) argument requires a value.
    :param incrementable:
        Whether or not this (``int``) argument is to be incremented instead of
        overwritten/assigned to.
    :param attr_name:
        A Python identifier/attribute friendly name, typically filled in with
        the underscored version when ``name``/``names`` contain dashes.

    .. versionadded:: 1.0
    """

    def __init__(
        self,
        name: Optional[str] = None,
        names: Iterable[str] = (),
        kind: Any = str,
        default: Optional[Any] = None,
        help: Optional[str] = None,
        positional: bool = False,
        optional: bool = False,
        incrementable: bool = False,
        attr_name: Optional[str] = None,
    ) -> None:
        if name and names:
            raise TypeError(
                "Cannot give both 'name' and 'names' arguments! Pick one."
            )
        if not (name or names):
            raise TypeError("An Argument must have at least one name.")
        if names:
            self.names = tuple(names)
        elif name and not names:
            self.names = (name,)
        self.kind = kind
        initial_value: Optional[Any] = None
        # Special case: list-type args start out as empty list, not None.
        if kind is list:
            initial_value = []
        # Another: incrementable args start out as their default value.
        if incrementable:
            initial_value = default
        self.raw_value = self._value = initial_value
        self.default = default
        self.help = help
        self.positional = positional
        self.optional = optional
        self.incrementable = incrementable
        self.attr_name = attr_name

    def __repr__(self) -> str:
        nicks = ""
        if self.nicknames:
            nicks = " ({})".format(", ".join(self.nicknames))
        flags = ""
        if self.positional or self.optional:
            flags = " "
        if self.positional:
            flags += "*"
        if self.optional:
            flags += "?"
        # TODO: store this default value somewhere other than signature of
        # Argument.__init__?
        kind = ""
        if self.kind != str:
            kind = " [{}]".format(self.kind.__name__)
        return "<{}: {}{}{}{}>".format(
            self.__class__.__name__, self.name, nicks, kind, flags
        )

    @property
    def name(self) -> Optional[str]:
        """
        The canonical attribute-friendly name for this argument.

        Will be ``attr_name`` (if given to constructor) or the first name in
        ``names`` otherwise.

        .. versionadded:: 1.0
        """
        return self.attr_name or self.names[0]

    @property
    def nicknames(self) -> Tuple[str, ...]:
        return self.names[1:]

    @property
    def takes_value(self) -> bool:
        if self.kind is bool:
            return False
        if self.incrementable:
            return False
        return True

    @property
    def value(self) -> Any:
        # TODO: should probably be optional instead
        return self._value if self._value is not None else self.default

    @value.setter
    def value(self, arg: str) -> None:
        self.set_value(arg, cast=True)

    def set_value(self, value: Any, cast: bool = True) -> None:
        """
        Actual explicit value-setting API call.

        Sets ``self.raw_value`` to ``value`` directly.

        Sets ``self.value`` to ``self.kind(value)``, unless:

        - ``cast=False``, in which case the raw value is also used.
        - ``self.kind==list``, in which case the value is appended to
          ``self.value`` instead of cast & overwritten.
        - ``self.incrementable==True``, in which case the value is ignored and
          the current (assumed int) value is simply incremented.

        .. versionadded:: 1.0
        """
        self.raw_value = value
        # Default to do-nothing/identity function
        func = lambda x: x
        # If cast, set to self.kind, which should be str/int/etc
        if cast:
            func = self.kind
        # If self.kind is a list, append instead of using cast func.
        if self.kind is list:
            func = lambda x: self.value + [x]
        # If incrementable, just increment.
        if self.incrementable:
            # TODO: explode nicely if self.value was not an int to start
            # with
            func = lambda x: self.value + 1
        self._value = func(value)

    @property
    def got_value(self) -> bool:
        """
        Returns whether the argument was ever given a (non-default) value.

        For most argument kinds, this simply checks whether the internally
        stored value is non-``None``; for others, such as ``list`` kinds,
        different checks may be used.

        .. versionadded:: 1.3
        """
        if self.kind is list:
            return bool(self._value)
        return self._value is not None
