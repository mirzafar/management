from datetime import datetime

from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class VisitsLessonsItemView(BaseAPIView):
    async def get(self, request, user, visit_id, lesson_id):
        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return self.error(message='Отсуствует обязательный параметр "lesson_id"')

        lesson = await db.fetchrow(
            '''
            SELECT *, to_char(time, 'YYYY-MM-DD"T"HH24:MI') AS time_str
            FROM public.visit_lessons
            WHERE id = $1
            ''',
            lesson_id
        ) or {}

        return self.success(data={
            'lesson': dict(lesson)
        })

    async def delete(self, request, user, visit_id, lesson_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметр "visit_id"')

        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return self.error(message='Отсуствует обязательный параметр "lesson_id"')

        item = await db.fetchrow(
            '''
            DELETE FROM public.visit_lessons
            WHERE id = $1
            RETURNING *
            ''',
            lesson_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        await db.execute(
            '''
            UPDATE public.visits
            SET count_lesson = count_lesson - 1
            WHERE id = $1
            ''',
            visit_id
        )

        return self.success()

    async def put(self, request, user, visit_id, lesson_id):
        lesson_id = IntUtils.to_int(lesson_id)
        if not lesson_id:
            return self.error(message='Отсуствует обязательный параметр "lesson_id"')

        description = StrUtils.to_str(request.json.get('description'))
        user_id = IntUtils.to_int(request.json.get('user_id'))
        time = DatetimeUtils.str_2_datetime(request.json.get('time'), '%Y-%m-%dT%H:%M') or datetime.now()

        item = await db.fetchrow(
            '''
            UPDATE public.visit_lessons
            SET description = $2, time = $3, user_id = $4, date_key = $5
            WHERE id = $1
            RETURNING *
            ''',
            lesson_id,
            description,
            time,
            user_id,
            str(time.date())
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
