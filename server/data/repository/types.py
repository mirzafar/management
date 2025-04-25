import ujson

from core.cache import cache
from core.db import mongo


class ControlTypesRepository:
    @classmethod
    async def get_types(cls):
        types = await cache.get('control:types')
        if types:
            return ujson.loads(types)

        types = {}
        items = await mongo.types.find({'is_active': True}).to_list(length=None)
        for item in items:
            types[str(item['_id'])] = {
                '_id': str(item['_id']),
                'title': item['title']
            }

        if types:
            await cache.set('control:types', ujson.dumps(types))

        return types

    @classmethod
    async def delete_cache(cls):
        return await cache.delete('control:types')
