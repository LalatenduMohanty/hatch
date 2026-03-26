import warnings


def hookimpl(func=None, **kwargs):
    """No-op decorator maintained for backward compatibility.

    This decorator does nothing and simply returns the decorated function unchanged.
    The hook system uses naming conventions only: any function or method whose name
    starts with ``hatch_register_`` is automatically discovered and registered.
    """
    if kwargs:
        warnings.warn(
            "hookimpl keyword arguments (e.g. tryfirst, trylast) are no longer supported "
            "and will be ignored. Hatchling now uses convention-based hook discovery.",
            DeprecationWarning,
            stacklevel=2,
        )

    if func is not None:
        return func

    def decorator(f):
        return f

    return decorator
