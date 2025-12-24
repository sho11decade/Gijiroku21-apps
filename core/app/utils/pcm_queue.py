import asyncio
from typing import AsyncGenerator, Optional


_queue: asyncio.Queue[bytes] = asyncio.Queue()
_closed = False


def reset() -> None:
    global _closed
    _closed = False
    while not _queue.empty():
        try:
            _queue.get_nowait()
        except asyncio.QueueEmpty:
            break


def close() -> None:
    global _closed
    _closed = True


def push(data: bytes) -> None:
    if _closed:
        return
    _queue.put_nowait(data)


async def stream(timeout: float = 5.0) -> AsyncGenerator[Optional[bytes], None]:
    while True:
        if _closed:
            break
        try:
            chunk = await asyncio.wait_for(_queue.get(), timeout=timeout)
            yield chunk
        except asyncio.TimeoutError:
            # emit None as heartbeat to allow consumer to continue
            yield None
    # when closed, drain remaining
    while not _queue.empty():
        try:
            yield _queue.get_nowait()
        except asyncio.QueueEmpty:
            break
