from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class VisitsReasonsView(BaseAPIView):
    template_name = 'admin/visits-reasons.html'

    async def get(self, request, user):
        reasons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title, description, price
            FROM public.visit_reasons
            WHERE is_active
            ORDER BY id DESC
            '''
        ))

        return self.success(request=request, user=user, data={
            'reasons': reasons,
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        price = IntUtils.to_int(request.json.get('price'), default=0)

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        item = await db.fetchrow(
            '''
            INSERT INTO public.visit_reasons
            (title, description, price)
            VALUES ($1, $2, $3)
            RETURNING *
            ''',
            title,
            description,
            abs(price)
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
