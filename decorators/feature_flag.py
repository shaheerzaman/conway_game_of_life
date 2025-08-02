import json
from functools import wraps

FEATURE_FLAGS = {
    "use_new_search_algorithm": True,
    "enable_beta_dashboard": False,
    "enable_chat_feature_for_user_101": True,
}


def feature_flagged(flag_name: str, fallback_func=None):
    """
    Decorator to enable/disable a function based on a feature flag.
    It can also check for user-specific flags.
    """

    def decorator(fun):
        s
