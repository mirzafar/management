import functools
from typing import Union

import openai
from openai import AsyncOpenAI

from local_settings import settings


class AiClient:
    client = None

    async def initialize(self):
        self.client = AsyncOpenAI(
            api_key=settings['ai_api_key']
        )

    def __getattr__(self, attr):
        return functools.partial(getattr(self.pool, attr))


ai_client = AiClient()  # type: Union[openai.AsyncOpenAI, AiClient]
