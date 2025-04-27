import asyncio
import traceback
from datetime import datetime, timedelta

from pymongo import UpdateOne
from sanic import Sanic

from core.db import mongo

app = Sanic(name='checker')


@app.before_server_start
async def before_server_start(_app, _loop):
    mongo.initialize(_loop)
    _loop.create_task(start())


async def start():
    while True:
        try:
            now = datetime.now() - timedelta(days=1)
            dtn = datetime(now.year, now.month, now.day)

            items = await mongo.receipts.find({
                '$or': [
                    {'billed_at': {'$in': [None, '']}},
                    {'billed_at': {'$exists': False}},
                ]
            }).to_list(length=None) or []

            operations = []
            for item in items:
                operations.append(UpdateOne(
                    filter={'receipt_id': str(item['_id']), 'dtn': dtn},
                    update={'$set': {
                        'company_id': item.get('company_id') and str(item['company_id']) or None,
                        'road_id': item.get('road_id') and str(item['road_id']) or None,
                        'event': 'stay'
                    }},
                    upsert=True
                ))

            if operations:
                await mongo.lagging_receipts.bulk_write(operations)


        except (Exception,):
            traceback.print_exc()

        await asyncio.sleep(int(timedelta(minutes=15).total_seconds()))


if __name__ == '__main__':
    try:
        app.run('0.0.0.0', port=8800, access_log=False)
    except (Exception,):
        traceback.print_exc()
