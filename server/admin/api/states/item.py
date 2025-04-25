from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.states import ControlStatesRepository
from utils.strs import StrUtils


class StateView(BaseAPIView):
    template_name = 'admin/states-item.html'

    async def get(self, request, user, state_id):
        state_id = StrUtils.to_str(state_id)
        if not state_id or not ObjectId.is_valid(state_id):
            return self.error(message='Отсуствует обязательный параметр "state_id"')

        state = await mongo.states.find_one({'_id': ObjectId(state_id)})

        return self.success(request=request, user=user, data={
            'state': state
        })

    async def put(self, request, user, state_id):
        state_id = StrUtils.to_str(state_id)
        if not state_id or not ObjectId.is_valid(state_id):
            return self.error(message='Отсуствует обязательный параметр "state_id"')

        title = StrUtils.to_str(request.json.get('title'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        await mongo.states.update_one({'_id': ObjectId(state_id)}, {'$set': {
            'title': title
        }})
        await ControlStatesRepository.delete_cache()

        return self.success()

    async def delete(self, request, user, state_id):
        state_id = StrUtils.to_str(state_id)
        if not state_id or not ObjectId.is_valid(state_id):
            return self.error(message='Отсуствует обязательный параметр "state_id"')

        await mongo.states.update_one({'_id': ObjectId(state_id)}, {'$set': {
            'is_active': False
        }})
        await ControlStatesRepository.delete_cache()
        return self.success()
