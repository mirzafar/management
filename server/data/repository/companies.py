import ujson

from core.cache import cache
from core.db import mongo


class ControlCompaniesRepository:
    @classmethod
    async def delete_cache(cls):
        return await cache.delete('control:companies')

    @classmethod
    async def get_companies(cls) -> dict:
        companies = await cache.get('control:companies')
        if companies:
            return ujson.loads(companies)

        companies = {}
        items = await mongo.companies.find({'is_active': True}).to_list(length=None)
        for item in items:
            companies[str(item['_id'])] = {
                '_id': str(item['_id']),
                'title': item['title'],
                'sum_cleaning': item.get('sum_cleaning'),
                'sum_stay': item.get('sum_stay'),
                'sum_weighing': item.get('sum_weighing'),
                'sum_rent_scale': item.get('sum_rent_scale'),
                'sum_rent_m': item.get('sum_rent_m'),
            }

        if companies:
            await cache.set('control:companies', ujson.dumps(companies))

        return companies
