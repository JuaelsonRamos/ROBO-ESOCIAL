"""Definição de como executar a aplicação que será simplemesmente rodada pelo entrypoint to
executável."""

from src.async_vitals.processes import Fork

__all__ = ["app"]


def app() -> None:
    p = Fork()
    try:
        for proc in p.processes:
            proc.join()
    finally:
        for proc in p.processes:
            proc.kill()
