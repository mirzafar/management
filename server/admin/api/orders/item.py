from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class OrderView(BaseAPIView):
    async def post(self, request, user, order_id):
        order_id = StrUtils.to_str(order_id)
        if not order_id or not ObjectId.is_valid(order_id):
            return self.error(message='Отсуствует обязательный параметр "good_id"')

        action = StrUtils.to_str(request.json.get('action'))

        if action == 'change_state':
            state = StrUtils.to_str(request.json.get('state'))
            if not state:
                return self.error(message='Отсуствует обязательный параметр "state"')

            await mongo.orders.update_one({'_id': ObjectId(order_id)}, {'$set': {
                'state': state
            }})

        return self.success()
