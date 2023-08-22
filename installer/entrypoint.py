"""Entrypoint do executável."""

from src.async_vitals.processes import Fork

if __name__ == "__main__":
    try:
        p = Fork()
        for proc in p.processes:
            proc.join()
    finally:
        for proc in p.processes:
            proc.kill()
