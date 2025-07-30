from datetime import datetime

from core.ai import ai_client
from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class FilesView(BaseAPIView):
    template_name = 'admin/files.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True,
            'user_id': user['id'],
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.files.find(filters).to_list(length=None)

        return self.success(request=request, user=user, data={
            'items': items
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.form.get('title'))
        file_url = StrUtils.to_str(request.form.get('url'))
        file = request.files['file']

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        if not file_url:
            return self.error(message='Отсуствует обязательный параметры "Файл url"')

        if not file:
            return self.error(message='Отсуствует обязательный параметры "Файл"')

        count = await mongo.files.count_documents({'is_active': True}) or 0
        if count > 20:
            return self.error(message='Файл больше лимита. Лимит: 20')

        file = file[0]
        try:
            upload_file = await ai_client.files.create(
                file=(file.name, file.body),
                purpose='assistants'
            )
        except (Exception,):
            return self.error(message='Не удалось загрузить файл')

        data = {
            'title': title,
            'file_url': file_url,
            'is_active': True,
            'user_id': user['id'],
            'upload_file_id': upload_file.id,
            'created_at': datetime.now()
        }

        inserted = await mongo.files.insert_one(data)

        if inserted.inserted_id:
            pass
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'item': data
        })
