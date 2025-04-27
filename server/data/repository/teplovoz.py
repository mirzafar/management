import ujson

from core.cache import cache
from core.db import mongo


class ControlTeplovozRepository:
    @classmethod
    async def get_teplovoz(cls):
        teplovoz = await cache.get('control:teplovoz')
        if teplovoz:
            return ujson.loads(teplovoz)

        teplovoz = {}
        items = await mongo.teplovoz.find({'is_active': True}).to_list(length=None)
        for item in items:
            teplovoz[str(item['_id'])] = {
                '_id': str(item['_id']),
                'title': item['title']
            }

        if teplovoz:
            await cache.set('control:teplovoz', ujson.dumps(teplovoz))

        return teplovoz

    @classmethod
    async def delete_cache(cls):
        return await cache.delete('control:teplovoz')
