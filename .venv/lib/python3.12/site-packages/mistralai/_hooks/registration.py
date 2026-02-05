from .custom_user_agent import CustomUserAgentHook
from .deprecation_warning import DeprecationWarningHook
from .tracing import TracingHook
from .types import Hooks

# This file is only ever generated once on the first generation and then is free to be modified.
# Any hooks you wish to add should be registered in the init_hooks function. Feel free to define them
# in this file or in separate files in the hooks folder.


def init_hooks(hooks: Hooks):
    # pylint: disable=unused-argument
    """Add hooks by calling hooks.register{sdk_init/before_request/after_success/after_error}Hook
    with an instance of a hook that implements that specific Hook interface
    Hooks are registered per SDK instance, and are valid for the lifetime of the SDK instance
    """
    tracing_hook = TracingHook()
    hooks.register_before_request_hook(CustomUserAgentHook())
    hooks.register_after_success_hook(DeprecationWarningHook())
    hooks.register_after_success_hook(tracing_hook)
    hooks.register_before_request_hook(tracing_hook)
    hooks.register_after_error_hook(tracing_hook)
