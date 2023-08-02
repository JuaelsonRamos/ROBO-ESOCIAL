from typing import NewType, Tuple

SeletorHTML = NewType("SeletorHTML", Tuple[str, str])
CelulaVaziaType = NewType("CelulaVaziaType", float)
CelulaVazia: CelulaVaziaType = float("nan")
