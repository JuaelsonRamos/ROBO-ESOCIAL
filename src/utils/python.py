import sys

__all__ = ["DEBUG"]

DEBUG: bool = hasattr(sys, "gettrace") and (sys.gettrace() is not None)
