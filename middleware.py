import asyncio
from typing import Callable

from aiogram import BaseMiddleware
from aiogram.types import Message


class AlbumMiddleware(BaseMiddleware):
    def __init__(self, latency=0.1):
        self.album = {}
        self.latency = latency

    async def __call__(self, handler: Callable, event: Message, data: dict):
        if not event.media_group_id:
            await handler(event, data)

        elif event.media_group_id not in self.album:
            self.album[event.media_group_id] = [event]
            await asyncio.sleep(self.latency)
            data['albums'] = self.album
            await handler(event, data)
            del self.album[event.media_group_id]
        else:
            self.album[event.media_group_id].append(event)
