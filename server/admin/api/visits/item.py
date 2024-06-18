from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class VisitsItemView(BaseAPIView):
    template_name = 'admin/visits-item.html'

    async def get(self, request, user, visit_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметр "visit_id"')

        visit = await db.fetchrow(
            '''
            SELECT *
            FROM public.visits
            WHERE id = $1
            ''',
            visit_id
        ) or {}

        lessons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.visit_lessons
            WHERE visit_id = $1
            ORDER BY id DESC
            ''',
            visit_id
        ))

        return self.success(request=request, user=user, data={
            'visit': dict(visit),
            'lessons': lessons
        })

    async def put(self, request, user, visit_id):
        reason = StrUtils.to_str(request.json.get('reason'))
        description = StrUtils.to_str(request.json.get('description'))
        user_id = IntUtils.to_int(request.json.get('user_id'))
        state_id = IntUtils.to_int(request.json.get('state_id'))
        time = DatetimeUtils.parse(request.json.get('time'))

        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметр "visit_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.visits
            SET reason = $2, description = $3, user_id = $4, time = $5, state_id = $6
            WHERE id = $1
            RETURNING *
            ''',
            visit_id,
            reason,
            description,
            user_id,
            time,
            state_id
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, visit_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметр "visit_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.visits
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            visit_id,
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()
