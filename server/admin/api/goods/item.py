from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.goods import ControlGoodsRepository
from utils.floats import FloatUtils
from utils.strs import StrUtils


class GoodView(BaseAPIView):
    async def get(self, request, user, good_id):
        good_id = StrUtils.to_str(good_id)
        if not good_id or not ObjectId.is_valid(good_id):
            return self.error(message='Отсуствует обязательный параметр "good_id"')

        good = await mongo.goods.find_one({'_id': ObjectId(good_id)})

        return self.success(data={
            'good': good
        })

    async def put(self, request, user, good_id):
        good_id = StrUtils.to_str(good_id)
        if not good_id or not ObjectId.is_valid(good_id):
            return self.error(message='Отсуствует обязательный параметр "good_id"')

        title = StrUtils.to_str(request.json.get('title'))
        price = FloatUtils.to_float(request.json.get('price'))
        description = StrUtils.to_str(request.json.get('description'))
        photo = StrUtils.to_str(request.json.get('photo'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        if not price:
            return self.error(message='Отсуствует обязательный параметры "Цена"')

        await mongo.goods.update_one({'_id': ObjectId(good_id)}, {'$set': {
            'title': title,
            'price': price,
            'description': description,
            'photo': photo
        }})
        await ControlGoodsRepository.delete_cache()

        return self.success()

    async def delete(self, request, user, good_id):
        good_id = StrUtils.to_str(good_id)
        if not good_id or not ObjectId.is_valid(good_id):
            return self.error(message='Отсуствует обязательный параметр "good_id"')

        await mongo.goods.update_one({'_id': ObjectId(good_id)}, {'$set': {
            'is_active': False
        }})

        await ControlGoodsRepository.delete_cache()
        return self.success()
