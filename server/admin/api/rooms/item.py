from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.types import ControlTypesRepository
from utils.floats import FloatUtils
from utils.strs import StrUtils


class RoomView(BaseAPIView):
    # template_name = 'admin/types-item.html'

    async def get(self, request, user, room_id):
        room_id = StrUtils.to_str(room_id)
        if not room_id or not ObjectId.is_valid(room_id):
            return self.error(message='Отсуствует обязательный параметр "room_id"')

        room = await mongo.rooms.find_one({'_id': ObjectId(room_id)})

        return self.success(request=request, user=user, data={
            'room': room
        })

    async def put(self, request, user, room_id):
        room_id = StrUtils.to_str(room_id)
        if not room_id or not ObjectId.is_valid(room_id):
            return self.error(message='Отсуствует обязательный параметр "room_id"')

        title = StrUtils.to_str(request.json.get('title'))
        summ = FloatUtils.to_float(request.json.get('summ'), default=0)

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        await mongo.rooms.update_one({'_id': ObjectId(room_id)}, {'$set': {
            'title': title,
            'summ': summ
        }})
        await ControlTypesRepository.delete_cache()

        return self.success()

    async def delete(self, request, user, room_id):
        room_id = StrUtils.to_str(room_id)
        if not room_id or not ObjectId.is_valid(room_id):
            return self.error(message='Отсуствует обязательный параметр "room_id"')

        room = await mongo.rooms.find_one({'_id': ObjectId(room_id)})
        if not room:
            return self.error(message='Не найдено')

        if room.get('in_use') is True:
            return self.error(message='Стол пока занят')

        await mongo.rooms.update_one({'_id': ObjectId(room_id)}, {'$set': {
            'is_active': False
        }})

        await ControlTypesRepository.delete_cache()
        return self.success()
