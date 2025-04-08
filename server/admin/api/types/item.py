from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class TypeView(BaseAPIView):
    template_name = 'admin/types-item.html'

    async def get(self, request, user, type_id):
        type_id = StrUtils.to_str(type_id)
        if not type_id or not ObjectId.is_valid(type_id):
            return self.error(message='Отсуствует обязательный параметр "type_id"')

        _type = await mongo.types.find_one({'_id': ObjectId(type_id)})

        return self.success(request=request, user=user, data={
            'type': _type
        })

    async def put(self, request, user, type_id):
        type_id = StrUtils.to_str(type_id)
        if not type_id or not ObjectId.is_valid(type_id):
            return self.error(message='Отсуствует обязательный параметр "type_id"')

        title = StrUtils.to_str(request.json.get('title'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        await mongo.types.update_one({'_id': ObjectId(type_id)}, {'$set': {
            'title': title
        }})

        return self.success()

    async def delete(self, request, user, type_id):
        type_id = StrUtils.to_str(type_id)
        if not type_id or not ObjectId.is_valid(type_id):
            return self.error(message='Отсуствует обязательный параметр "type_id"')

        await mongo.types.update_one({'_id': ObjectId(type_id)}, {'$set': {
            'is_active': False
        }})

        return self.success()
