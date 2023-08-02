import sys

DEBUG: bool = hasattr(sys, "gettrace") and (sys.gettrace() is not None)
