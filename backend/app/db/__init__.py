from .session import get_engine, get_session

# For backwards compatibility, expose engine as a function call
engine = property(lambda self: get_engine())

__all__ = ["get_engine", "get_session", "engine"]
