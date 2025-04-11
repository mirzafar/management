from datetime import datetime

from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.ints import IntUtils
from utils.strs import StrUtils


class RoadsView(BaseAPIView):
    template_name = 'admin/roads.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 50))
        offset = IntUtils.to_int(request.args.get('offset')) or pager.offset

        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.roads.find(filters).skip(offset) \
            .limit(pager.limit) \
            .sort('_id', -1) \
            .to_list(length=None)

        return self.success(request=request, user=user, data={
            'roads': items
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        data = {
            'title': title,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.roads.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'roads': data
        })
