import ujson

from core.cache import cache
from core.db import mongo


class ControlRoadsRepository:
    @classmethod
    async def get_roads(cls):
        roads = await cache.get('control:roads')
        if roads:
            return ujson.loads(roads)

        roads = {}
        items = await mongo.roads.find({'is_active': True}).to_list(length=None)
        for item in items:
            roads[str(item['_id'])] = {
                '_id': str(item['_id']),
                'title': item['title']
            }

        if roads:
            await cache.set('control:roads', ujson.dumps(roads))

        return roads

    @classmethod
    async def delete_cache(cls):
        return await cache.delete('control:roads')