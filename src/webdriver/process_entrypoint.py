__all__ = ["webdriver_process_entrypoint"]


def webdriver_process_entrypoint(
    to_process_queue: object,
    done_queue: object,
    started_event: object,
    progress_values: object,
) -> None:
    from src.webdriver.main import main

    main(to_process_queue, done_queue, started_event, progress_values)
