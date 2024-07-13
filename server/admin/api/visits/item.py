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
            SELECT id, description, client_id, count_lesson, reason_id, percent_process, is_active
            FROM public.visits
            WHERE id = $1
            ''',
            visit_id
        ) or {}

        lessons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT v.*, jsonb_build_object(
                    'id', u.id,
                    'first_name', u.first_name,
                    'last_name', u.last_name,
                    'photo', u.photo,
                    'username', u.username
                ) AS employee
            FROM public.visit_lessons v
            LEFT JOIN users u on v.user_id = u.id
            WHERE v.visit_id = $1
            ORDER BY v.time DESC
            ''',
            visit_id
        ))

        return self.success(request=request, user=user, data={
            'visit': dict(visit),
            'lessons': lessons
        })

    async def put(self, request, user, visit_id):
        reason_id = IntUtils.to_int(request.json.get('reason_id'))
        description = StrUtils.to_str(request.json.get('description'))

        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметр "visit_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.visits
            SET reason_id = $2, description = $3
            WHERE id = $1
            RETURNING *
            ''',
            visit_id,
            reason_id,
            description
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
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *
            ''',
            visit_id,
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'visit': dict(data)
        })
