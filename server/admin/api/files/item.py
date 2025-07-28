from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class FileView(BaseAPIView):
    async def get(self, request, user, file_id):
        file_id = StrUtils.to_str(file_id)
        if not file_id or not ObjectId.is_valid(file_id):
            return self.error(message='Отсуствует обязательный параметр "file_id"')

        file = await mongo.files.find_one({'_id': ObjectId(file_id)})

        return self.success(data={
            'item': file
        })

    async def put(self, request, user, file_id):
        file_id = StrUtils.to_str(file_id)
        if not file_id or not ObjectId.is_valid(file_id):
            return self.error(message='Отсуствует обязательный параметр "file_id"')

        title = StrUtils.to_str(request.json.get('title'))
        file_url = StrUtils.to_str(request.json.get('file'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        if not file_url:
            return self.error(message='Отсуствует обязательный параметры "Ссылка"')

        await mongo.files.update_one({'_id': ObjectId(file_id)}, {'$set': {
            'title': title,
            'file_url': file_url
        }})

        return self.success()

    async def delete(self, request, user, file_id):
        file_id = StrUtils.to_str(file_id)
        if not file_id or not ObjectId.is_valid(file_id):
            return self.error(message='Отсуствует обязательный параметр "file_id"')

        await mongo.files.update_one({'_id': ObjectId(file_id)}, {'$set': {
            'is_active': False
        }})

        return self.success()
