from typing import Tuple, NewType

SeletorHTML = NewType("SeletorHTML", Tuple[str, str])
CelulaVaziaType = NewType("CelulaVaziaType", float)
CelulaVazia: CelulaVaziaType = float("nan")