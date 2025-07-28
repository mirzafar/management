from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class ChatView(BaseAPIView):
    async def get(self, request, user, chat_id):
        chat_id = StrUtils.to_str(chat_id)
        if not chat_id or not ObjectId.is_valid(chat_id):
            return self.error(message='Отсуствует обязательный параметр "chat_id"')

        chat = await mongo.chats.find_one({'_id': ObjectId(chat_id)})

        return self.success(data={
            'item': chat
        })
