from datetime import datetime

from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from utils.bools import BoolUtils
from utils.floats import FloatUtils
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
        time = DatetimeUtils.str_2_datetime(request.json.get('time'), '%Y-%m-%dT%H:%M') or datetime.now()
        price = FloatUtils.to_float(request.json.get('price'))

        item = await db.fetchrow(
            '''
            INSERT INTO public.visit_lessons
            (user_id, visit_id, description, time, date_key, price)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            ''',
            user_id,
            visit_id,
            description,
            time,
            str(time.date()),
            price
        )

        if not item:
            return self.error(message='Операция не выполнена')

        await db.execute(
            '''
            UPDATE public.visits
            SET count_lesson = count_lesson + 1
            WHERE id = $1
            ''',
            visit_id
        )

        return self.success()
