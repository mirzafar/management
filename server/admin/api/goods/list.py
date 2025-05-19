from datetime import datetime

from pymongo import ReturnDocument

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.goods import ControlGoodsRepository
from utils.floats import FloatUtils
from utils.strs import StrUtils


class GoodsView(BaseAPIView):
    template_name = 'admin/goods.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.goods.find(filters).to_list(length=None)

        return self.success(request=request, user=user, data={
            'goods': items
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        price = FloatUtils.to_float(request.json.get('price'))
        description = StrUtils.to_str(request.json.get('description'))
        photo = StrUtils.to_str(request.json.get('photo'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        if not price:
            return self.error(message='Отсуствует обязательный параметры "Цена"')

        counter = await mongo.counters.find_one_and_update(
            filter={'collection': 'goods'},
            update={'$inc': {'seq': 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        data = {
            'id': counter['seq'],
            'title': title,
            'price': price,
            'description': description,
            'photo': photo,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.goods.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
            await ControlGoodsRepository.delete_cache()
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'goods': data
        })
