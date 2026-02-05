"""
Environment variable configuration loading class.

Using a class here doesn't really model anything but makes state passing (in a
situation requiring it) more convenient.

This module is currently considered private/an implementation detail and should
not be included in the Sphinx API documentation.
"""

import os
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Mapping, Sequence

from .exceptions import UncastableEnvVar, AmbiguousEnvVar
from .util import debug

if TYPE_CHECKING:
    from .config import Config


class Environment:
    def __init__(self, config: "Config", prefix: str) -> None:
        self._config = config
        self._prefix = prefix
        self.data: Dict[str, Any] = {}  # Accumulator

    def load(self) -> Dict[str, Any]:
        """
        Return a nested dict containing values from `os.environ`.

        Specifically, values whose keys map to already-known configuration
        settings, allowing us to perform basic typecasting.

        See :ref:`env-vars` for details.
        """
        # Obtain allowed env var -> existing value map
        env_vars = self._crawl(key_path=[], env_vars={})
        m = "Scanning for env vars according to prefix: {!r}, mapping: {!r}"
        debug(m.format(self._prefix, env_vars))
        # Check for actual env var (honoring prefix) and try to set
        for env_var, key_path in env_vars.items():
            real_var = (self._prefix or "") + env_var
            if real_var in os.environ:
                self._path_set(key_path, os.environ[real_var])
        debug("Obtained env var config: {!r}".format(self.data))
        return self.data

    def _crawl(
        self, key_path: List[str], env_vars: Mapping[str, Sequence[str]]
    ) -> Dict[str, Any]:
        """
        Examine config at location ``key_path`` & return potential env vars.

        Uses ``env_vars`` dict to determine if a conflict exists, and raises an
        exception if so. This dict is of the following form::

            {
                'EXPECTED_ENV_VAR_HERE': ['actual', 'nested', 'key_path'],
                ...
            }

        Returns another dictionary of new keypairs as per above.
        """
        new_vars: Dict[str, List[str]] = {}
        obj = self._path_get(key_path)
        # Sub-dict -> recurse
        if (
            hasattr(obj, "keys")
            and callable(obj.keys)
            and hasattr(obj, "__getitem__")
        ):
            for key in obj.keys():
                merged_vars = dict(env_vars, **new_vars)
                merged_path = key_path + [key]
                crawled = self._crawl(merged_path, merged_vars)
                # Handle conflicts
                for key in crawled:
                    if key in new_vars:
                        err = "Found >1 source for {}"
                        raise AmbiguousEnvVar(err.format(key))
                # Merge and continue
                new_vars.update(crawled)
        # Other -> is leaf, no recursion
        else:
            new_vars[self._to_env_var(key_path)] = key_path
        return new_vars

    def _to_env_var(self, key_path: Iterable[str]) -> str:
        return "_".join(key_path).upper()

    def _path_get(self, key_path: Iterable[str]) -> "Config":
        # Gets are from self._config because that's what determines valid env
        # vars and/or values for typecasting.
        obj = self._config
        for key in key_path:
            obj = obj[key]
        return obj

    def _path_set(self, key_path: Sequence[str], value: str) -> None:
        # Sets are to self.data since that's what we are presenting to the
        # outer config object and debugging.
        obj = self.data
        for key in key_path[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        old = self._path_get(key_path)
        new = self._cast(old, value)
        obj[key_path[-1]] = new

    def _cast(self, old: Any, new: Any) -> Any:
        if isinstance(old, bool):
            return new not in ("0", "")
        elif isinstance(old, str):
            return new
        elif old is None:
            return new
        elif isinstance(old, (list, tuple)):
            err = "Can't adapt an environment string into a {}!"
            err = err.format(type(old))
            raise UncastableEnvVar(err)
        else:
            return old.__class__(new)
