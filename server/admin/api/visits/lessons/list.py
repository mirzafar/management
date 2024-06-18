from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class VisitsLessonsView(BaseAPIView):
    template_name = 'admin/visits-lessons.html'

    async def post(self, request, user, visit_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметр "visit_id"')

        description = StrUtils.to_str(request.json.get('description'))
        user_id = IntUtils.to_int(request.json.get('user_id'))
        time = DatetimeUtils.str_2_datetime(request.json.get('time'), '%Y-%m-%dT%H:%M')

        item = await db.fetchrow(
            '''
            INSERT INTO public.visit_lessons
            (user_id, visit_id, description, time)
            VALUES ($1, $2, $3, $4)
            RETURNING *
            ''',
            user_id,
            visit_id,
            description,
            time
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
