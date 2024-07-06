from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils
from utils.strs import StrUtils


class VisitsReasonsView(BaseAPIView):
    template_name = 'admin/visits-reasons.html'

    async def get(self, request, user):
        reasons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.visit_reasons
            WHERE status = 1
            ORDER BY id DESC
            '''
        ))

        return self.success(request=request, user=user, data={
            'reasons': reasons,
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "title: str"')

        item = await db.fetchrow(
            '''
            INSERT INTO public.visit_reasons
            (title)
            VALUES ($1)
            RETURNING *
            ''',
            title
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
