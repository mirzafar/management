import asyncio

import asyncpg
import ujson
from motor import motor_asyncio

from settings import settings

__all__ = ['mongo', 'db']


class MongoProxy:
    db = None

    def __init__(self, url):
        self.url = url
        self.db_name = url.split('/')[-1]

    def initialize(self, loop):
        client = motor_asyncio.AsyncIOMotorClient(self.url, io_loop=loop)
        self.db = client[self.db_name]

    def __getattr__(self, item):
        return getattr(self.db, item)

    def __getitem__(self, item):
        return self.db[item]


class DBProxy:
    pool = None

    async def pool_connection_init(self, conn):
        await conn.set_type_codec(
            'jsonb',
            encoder=ujson.dumps,
            decoder=ujson.loads,
            schema='pg_catalog'
        )

        await conn.set_type_codec(
            'json',
            encoder=ujson.dumps,
            decoder=ujson.loads,
            schema='pg_catalog'
        )

    async def initialize(self, loop, min_size: int = 2, max_size: int = 15):
        loops = asyncio.get_event_loop_policy().get_event_loop()
        self.pool = await asyncpg.create_pool(
            init=self.pool_connection_init,
            min_size=min_size,
            max_size=max_size,
            command_timeout=300,
            loop=loop,
            **settings['db']
        )

    async def execute(self, *args, **kwargs):
        async with self.pool.acquire() as db:
            return await db.execute(*args, **kwargs)

    async def fetch(self, *args, **kwargs):
        async with self.pool.acquire() as db:
            return await db.fetch(*args, **kwargs)

    async def fetchrow(self, *args, **kwargs):
        async with self.pool.acquire() as db:
            return await db.fetchrow(*args, **kwargs)

    async def executemany(self, *args, **kwargs):
        async with self.pool.acquire() as db:
            return await db.executemany(*args, **kwargs)

    async def fetchval(self, *args, **kwargs):
        async with self.pool.acquire() as db:
            return await db.fetchval(*args, **kwargs)


MONGO_HOST = settings.get('mongo', {}).get('db_host')
MONGO_PORT = settings.get('mongo', {}).get('db_port')
MONGO_DATABASE = settings.get('mongo', {}).get('db_database')

mongo = MongoProxy(f'mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DATABASE}')
db = DBProxy()
