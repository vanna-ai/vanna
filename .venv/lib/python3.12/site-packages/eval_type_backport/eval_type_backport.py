from __future__ import annotations

import ast
import collections.abc
import contextlib
import functools
import re
import sys
import typing
import uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from _typeshed import Unused


def is_unsupported_types_for_union_error(e: TypeError) -> bool:
    return str(e).startswith('unsupported operand type(s) for |: ')


def is_not_subscriptable_error(e: TypeError) -> bool:
    return "' object is not subscriptable" in str(e)


def is_backport_fixable_error(e: TypeError) -> bool:
    return is_unsupported_types_for_union_error(e) or is_not_subscriptable_error(e)


# From https://peps.python.org/pep-0585/#implementation
new_generic_types = {
    tuple: 'Tuple',
    list: 'List',
    dict: 'Dict',
    set: 'Set',
    frozenset: 'FrozenSet',
    type: 'Type',
    collections.deque: 'Deque',
    collections.defaultdict: 'DefaultDict',
    collections.abc.Set: 'AbstractSet',
    contextlib.AbstractContextManager: 'ContextManager',
    contextlib.AbstractAsyncContextManager: 'AsyncContextManager',
    **{
        k: k.__name__
        for k in (
            collections.OrderedDict,
            collections.Counter,
            collections.ChainMap,
            collections.abc.Awaitable,
            collections.abc.Coroutine,
            collections.abc.AsyncIterable,
            collections.abc.AsyncIterator,
            collections.abc.AsyncGenerator,
            collections.abc.Iterable,
            collections.abc.Iterator,
            collections.abc.Generator,
            collections.abc.Reversible,
            collections.abc.Container,
            collections.abc.Collection,
            collections.abc.Callable,
            collections.abc.MutableSet,
            collections.abc.Mapping,
            collections.abc.MutableMapping,
            collections.abc.Sequence,
            collections.abc.MutableSequence,
            collections.abc.MappingView,
            collections.abc.KeysView,
            collections.abc.ItemsView,
            collections.abc.ValuesView,
            re.Pattern,
            re.Match,
        )
    },
}


class BackportTransformer(ast.NodeTransformer):
    """
    Transforms `X | Y` into `typing.Union[X, Y]`
    and `list[X]` into `typing.List[X]` etc.
    if the original syntax is not supported.
    """

    def __init__(
        self, globalns: dict[str, Any] | None, localns: Mapping[str, Any] | None
    ):
        # This logic for handling Nones is copied from typing.ForwardRef._evaluate
        if globalns is None and localns is None:
            globalns = localns = {}
        elif globalns is None:
            # apparently pyright doesn't infer this automatically
            assert localns is not None
            globalns = {**localns}
        elif localns is None:
            localns = globalns

        self.typing_name = f'typing_{uuid.uuid4().hex}'
        self.globalns = globalns
        self.localns = {**localns, self.typing_name: typing}

    def eval_type(
        self,
        node: ast.Expression | ast.expr,
        *,
        original_ref: typing.ForwardRef | None = None,
    ) -> Any:
        if not isinstance(node, ast.Expression):
            node = ast.copy_location(ast.Expression(node), node)
        ref = typing.ForwardRef(ast.dump(node))
        if original_ref:
            for attr in 'is_argument is_class module'.split():
                attr = f'__forward_{attr}__'
                if hasattr(original_ref, attr):
                    setattr(ref, attr, getattr(original_ref, attr))
        ref.__forward_code__ = compile(node, '<node>', 'eval')
        return typing._eval_type(  # type: ignore
            ref, self.globalns, self.localns
        )

    def visit_BinOp(self, node) -> ast.BinOp | ast.Subscript:
        node = self.generic_visit(node)
        assert isinstance(node, ast.BinOp)
        if isinstance(node.op, ast.BitOr):
            left_val = self.eval_type(node.left)
            right_val = self.eval_type(node.right)
            try:
                _ = left_val | right_val
            except TypeError as e:
                if not is_unsupported_types_for_union_error(e):
                    raise
                # Replace `left | right` with `typing.Union[left, right]`
                replacement = ast.Subscript(
                    value=ast.Attribute(
                        value=ast.Name(id=self.typing_name, ctx=ast.Load()),
                        attr='Union',
                        ctx=ast.Load(),
                    ),
                    slice=ast.Index(
                        value=ast.Tuple(elts=[node.left, node.right], ctx=ast.Load())
                    ),
                    ctx=ast.Load(),
                )
                return ast.fix_missing_locations(replacement)

        return node

    if sys.version_info[:2] < (3, 9):

        def visit_Subscript(self, node) -> ast.Subscript:
            node = self.generic_visit(node)
            assert isinstance(node, ast.Subscript)
            try:
                value_val = self.eval_type(node.value)
            except TypeError:
                # Likely typing._type_check complaining that the result isn't a type,
                # e.g. that it's a plain `Literal`.
                # Either way, this probably isn't one of the new generic types
                # that needs replacing.
                return node
            if value_val not in new_generic_types:
                return node
            replacement = ast.Subscript(
                value=ast.Attribute(
                    value=ast.Name(id=self.typing_name, ctx=ast.Load()),
                    attr=new_generic_types[value_val],
                    ctx=ast.Load(),
                ),
                slice=node.slice,
                ctx=ast.Load(),
            )
            return ast.fix_missing_locations(replacement)


original_evaluate = typing.ForwardRef._evaluate


if sys.version_info[:2] >= (3, 10):
    # On Python 3.10+, the original _evaluate already supports the new syntax
    ForwardRef = typing.ForwardRef  # type: ignore[misc]
else:

    class ForwardRef(typing.ForwardRef, _root=True):  # type: ignore[call-arg,misc]
        """
        Like `typing.ForwardRef`, but lets older Python versions use newer typing features.
        Specifically, when evaluated, this transforms `X | Y` into `typing.Union[X, Y]`
        and `list[X]` into `typing.List[X]` etc. (for all the types made generic in PEP 585)
        if the original syntax is not supported in the current Python version.
        """

        @functools.wraps(original_evaluate)
        def _evaluate(
            self,
            globalns: dict[str, Any] | None,
            localns: dict[str, Any] | None,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            try:
                return original_evaluate(self, globalns, localns, *args, **kwargs)
            except TypeError as e:
                if not is_backport_fixable_error(e):
                    raise
            return _eval_direct(self, globalns, localns)


def _eval_direct(
    value: typing.ForwardRef,
    globalns: dict[str, Any] | None = None,
    localns: Mapping[str, Any] | None = None,
):
    tree = ast.parse(value.__forward_arg__, mode='eval')
    transformer = BackportTransformer(globalns, localns)
    tree = transformer.visit(tree)
    return transformer.eval_type(tree, original_ref=value)


if sys.version_info[:2] >= (3, 10):
    def eval_type_backport(
        value: Any,
        globalns: dict[str, Any] | None = None,
        localns: Mapping[str, Any] | None = None,
        try_default: Unused = True,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Alias to typing._eval_type (Python 3.10+)."""
        return typing._eval_type(value, globalns, localns, *args, **kwargs)  # type: ignore

else:

    def eval_type_backport(
        value: Any,
        globalns: dict[str, Any] | None = None,
        localns: Mapping[str, Any] | None = None,
        try_default: bool = True,
    ) -> Any:
        """
        Like `typing._eval_type`, but lets older Python versions use newer typing features.
        Specifically, this transforms `X | Y` into `typing.Union[X, Y]`
        and `list[X]` into `typing.List[X]` etc. (for all the types made generic in PEP 585)
        if the original syntax is not supported in the current Python version.
        """
        if not try_default:
            return _eval_direct(value, globalns, localns)
        try:
            return typing._eval_type(  # type: ignore
                value, globalns, localns
            )
        except TypeError as e:
            if not (
                isinstance(value, typing.ForwardRef) and is_backport_fixable_error(e)
            ):
                raise
            return _eval_direct(value, globalns, localns)
