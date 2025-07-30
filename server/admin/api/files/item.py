import traceback

from bson import ObjectId
from pymongo import ReturnDocument

from core.ai import ai_client
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

    async def delete(self, request, user, file_id):
        file_id = StrUtils.to_str(file_id)
        if not file_id or not ObjectId.is_valid(file_id):
            return self.error(message='Отсуствует обязательный параметр "file_id"')

        file = await mongo.files.find_one_and_update({'_id': ObjectId(file_id)}, {'$set': {
            'is_active': False
        }}, return_document=ReturnDocument.AFTER)

        if file.get('upload_file_id'):
            try:
                await ai_client.files.delete(file['upload_file_id'])
            except (Exception,):
                traceback.print_exc()

        return self.success()
