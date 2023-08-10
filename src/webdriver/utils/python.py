""" Operações úteis e genérias relacionadas a linguagem Python."""

import sys

__all__ = ["DEBUG"]

DEBUG: bool = hasattr(sys, "gettrace") and (sys.gettrace() is not None)
""" Se o programa está sendo executado em modo de Debug."""
