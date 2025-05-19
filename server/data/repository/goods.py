import ujson

from core.cache import cache
from core.db import mongo


class ControlGoodsRepository:
    @classmethod
    async def delete_cache(cls):
        return await cache.delete('control:goods')

    @classmethod
    async def get_goods(cls) -> dict:
        goods = await cache.get('control:goods')
        if goods:
            return ujson.loads(goods)

        goods = {}
        items = await mongo.goods.find({'is_active': True}).to_list(length=None)
        for item in items:
            goods[str(item['id'])] = {
                '_id': str(item['_id']),
                'id': item['id'],
                'title': item['title'],
                'price': item['price'],
                'description': item['description'],
                'photo': item['photo'],
            }

        if goods:
            await cache.set('control:goods', ujson.dumps(goods))

        return goods
