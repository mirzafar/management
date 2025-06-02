from datetime import datetime

from pymongo import ReturnDocument

from core.db import mongo
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
from utils.strs import StrUtils


class RoomsView(BaseAPIView):
    template_name = 'admin/rooms.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.rooms.find(filters).sort('_id', -1).to_list(length=None)

        return self.success(request=request, user=user, data={
            'rooms': items
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        summ = FloatUtils.to_float(request.json.get('summ'), default=0)

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        if not summ:
            return self.error(message='Отсуствует обязательный параметры "Сумма"')

        counter = await mongo.counters.find_one_and_update(
            filter={'collection': 'goods'},
            update={'$inc': {'seq': 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        data = {
            'id': counter['seq'],
            'title': title,
            'summ': summ,
            'in_use': False,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.rooms.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'rooms': data
        })
