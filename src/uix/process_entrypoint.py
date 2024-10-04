"""Entrypoint para a interface gráfica.

Não importa nenhum código nem aloca nenhuma memória fora da função de entrypoint.
"""

__all__ = ["uix_process_entrypoint"]


def uix_process_entrypoint(
    to_process_queue: object,
    started_event: object,
    progress_values: object,
) -> None:
    """Entrypoint da interface gráfica."""
    import os
    from src.uix.app import CoralApp

    os.environ["KIVY_GL_BACKEND"] = "sdl2"
    CoralApp(to_process_queue, started_event, progress_values).run()
