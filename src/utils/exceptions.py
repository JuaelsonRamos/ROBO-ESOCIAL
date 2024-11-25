from __future__ import annotations


# NOTE __reduce__ é preferível e tem o mesmo efeito que __init__
# SEE https://stackoverflow.com/q/16244923/15493645


class EmptyString(ValueError): ...
