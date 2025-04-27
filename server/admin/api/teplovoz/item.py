from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.teplovoz import ControlTeplovozRepository
from utils.strs import StrUtils


class TeplovozItemView(BaseAPIView):
    template_name = 'admin/teplovoz-item.html'

    async def get(self, request, user, teplovoz_id):
        teplovoz_id = StrUtils.to_str(teplovoz_id)
        if not teplovoz_id or not ObjectId.is_valid(teplovoz_id):
            return self.error(message='Отсуствует обязательный параметр "teplovoz_id"')

        teplovoz = await mongo.teplovoz.find_one({'_id': ObjectId(teplovoz_id)})

        return self.success(request=request, user=user, data={
            'teplovoz': teplovoz
        })

    async def put(self, request, user, teplovoz_id):
        teplovoz_id = StrUtils.to_str(teplovoz_id)
        if not teplovoz_id or not ObjectId.is_valid(teplovoz_id):
            return self.error(message='Отсуствует обязательный параметр "teplovoz_id"')

        title = StrUtils.to_str(request.json.get('title'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        await mongo.teplovoz.update_one({'_id': ObjectId(teplovoz_id)}, {'$set': {
            'title': title
        }})
        await ControlTeplovozRepository.delete_cache()

        return self.success()

    async def delete(self, request, user, teplovoz_id):
        teplovoz_id = StrUtils.to_str(teplovoz_id)
        if not teplovoz_id or not ObjectId.is_valid(teplovoz_id):
            return self.error(message='Отсуствует обязательный параметр "teplovoz_id"')

        await mongo.teplovoz.update_one({'_id': ObjectId(teplovoz_id)}, {'$set': {
            'is_active': False
        }})
        await ControlTeplovozRepository.delete_cache()
        return self.success()
