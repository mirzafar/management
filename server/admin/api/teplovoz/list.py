from datetime import datetime

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.teplovoz import ControlTeplovozRepository
from utils.strs import StrUtils


class TeplovozView(BaseAPIView):
    template_name = 'admin/teplovoz.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.teplovoz.find(filters).sort('_id', -1).to_list(length=None)

        return self.success(request=request, user=user, data={
            'teplovoz': items
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

        inserted = await mongo.teplovoz.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
            await ControlTeplovozRepository.delete_cache()
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'teplovoz': data
        })
