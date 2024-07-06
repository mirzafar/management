from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class VisitsReasonsItemView(BaseAPIView):
    template_name = 'admin/visits-reason-item.html'

    async def get(self, request, user, reason_id):
        reason_id = IntUtils.to_int(reason_id)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметр "reason_id"')

        reason = await db.fetchrow(
            '''
            SELECT *
            FROM public.visit_reasons
            WHERE id = $1
            ''',
            reason_id
        ) or {}

        return self.success(request=request, user=user, data={
            'reason': dict(reason),
        })

    async def put(self, request, user, reason_id):
        reason_id = IntUtils.to_int(reason_id)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметр "reason_id"')

        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "title: str"')

        item = await db.fetchrow(
            '''
            UPDATE public.visit_reasons
            SET title = $2
            WHERE id = $1
            RETURNING *
            ''',
            reason_id,
            title
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, reason_id):
        reason_id = IntUtils.to_int(reason_id)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметр "reason_id"')

        item = await db.fetchrow(
            '''
            UPDATE public.visit_reasons
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            reason_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
