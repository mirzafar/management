from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class RoadView(BaseAPIView):
    template_name = 'admin/roads-item.html'

    async def get(self, request, user, road_id):
        road_id = StrUtils.to_str(road_id)
        if not road_id or not ObjectId.is_valid(road_id):
            return self.error(message='Отсуствует обязательный параметр "road_id"')

        road = await mongo.roads.find_one({'_id': ObjectId(road_id)})

        return self.success(request=request, user=user, data={
            'road': road
        })

    async def put(self, request, user, road_id):
        road_id = StrUtils.to_str(road_id)
        if not road_id or not ObjectId.is_valid(road_id):
            return self.error(message='Отсуствует обязательный параметр "road_id"')

        title = StrUtils.to_str(request.json.get('title'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        await mongo.roads.update_one({'_id': ObjectId(road_id)}, {'$set': {
            'title': title
        }})

        return self.success()

    async def delete(self, request, user, road_id):
        road_id = StrUtils.to_str(road_id)
        if not road_id or not ObjectId.is_valid(road_id):
            return self.error(message='Отсуствует обязательный параметр "road_id"')

        await mongo.roads.update_one({'_id': ObjectId(road_id)}, {'$set': {
            'is_active': False
        }})

        return self.success()
