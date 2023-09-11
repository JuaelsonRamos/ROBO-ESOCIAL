from aioprocessing.queues import AioQueue
from dataclasses import dataclass

__all__ = ["Queues"]


@dataclass(init=True, frozen=True)
class Queues:
    processing: AioQueue
