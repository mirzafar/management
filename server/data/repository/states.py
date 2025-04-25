import ujson

from core.cache import cache
from core.db import mongo


class ControlStatesRepository:
    @classmethod
    async def get_states(cls):
        states = await cache.get('control:states')
        if states:
            return ujson.loads(states)

        states = {}
        items = await mongo.states.find({'is_active': True}).to_list(length=None)
        for item in items:
            states[str(item['_id'])] = {
                '_id': str(item['_id']),
                'title': item['title']
            }

        if states:
            await cache.set('control:states', ujson.dumps(states))

        return states

    @classmethod
    async def delete_cache(cls):
        return await cache.delete('control:states')