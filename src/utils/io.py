from dataclasses import dataclass
from os.path import abspath, dirname, join

__all__ = ["PastasProjeto"]


@dataclass(init=False, frozen=True)
class PastasProjeto:
    """Pastas relacionadas ao próprio projeto (código fonte).

    :final:
    """

    root: str = abspath(join(dirname(__file__), "..", ".."))
    assets: str = join(root, "assets")
