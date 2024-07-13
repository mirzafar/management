from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.tools import order_date


class LessonsView(BaseAPIView):
    template_name = 'admin/lessons.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        employee_id = IntUtils.to_int(request.args.get('employee_id'))

        start_date, stop_date = order_date(
            request.args.get('start_date'),
            request.args.get('stop_date'),
            defu='last_day'
        )

        cond, cond_vars = ['vl.time BETWEEN {} AND {}'], [start_date, stop_date]

        if employee_id:
            cond.append('vl.user_id = {}')
            cond_vars.append(employee_id)

        cond, _ = set_counters(' AND '.join(cond))

        lessons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT  vl.id, 
                    vl.time, 
                    vl.room, 
                    is_cancel, 
                    is_finish, 
                    is_paid,
                    price,
                    jsonb_build_object(
                        'id', u.id,
                        'first_name', u.first_name,
                        'last_name', u.last_name,
                        'photo', u.photo,
                        'username', u.username
                    ) AS employee,
                    jsonb_build_object(
                        'id', c.id,
                        'first_name', c.first_name,
                        'last_name', c.last_name,
                        'photo', c.photo
                    ) AS client
            FROM public.visit_lessons vl
            LEFT JOIN public.users u ON u.id = vl.user_id
            LEFT JOIN public.visits v ON vl.visit_id = v.id
            LEFT JOIN public.clients c ON v.client_id = c.id
            WHERE vl.is_active AND %s
            ORDER BY vl.time DESC, vl.id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM public.visit_lessons vl
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'lessons': lessons,
            'pager': pager.dict(),
            'start_date': str(start_date.date()),
            'stop_date': str(stop_date.date()),
            'employee_id': employee_id
        })

    async def post(self, request, user):
        action = request.json.get('action')
        lesson_id = IntUtils.to_int(request.json.get('lesson_id'))
        if action == 'finish' and lesson_id:
            lesson = await db.fetchrow(
                '''
                UPDATE public.visit_lessons 
                SET is_finish = TRUE AND is_cancel = FALSE
                WHERE id = $1
                RETURNING *
                ''',
                lesson_id
            )

            if not lesson:
                return self.error(message='Операция не выполнена')

            return self.success()

        if action == 'cancel' and lesson_id:
            lesson = await db.fetchrow(
                '''
                UPDATE public.visit_lessons 
                SET is_cancel = TRUE, is_finish = FALSE
                WHERE id = $1
                RETURNING *
                ''',
                lesson_id
            )

            if not lesson:
                return self.error(message='Операция не выполнена')

            return self.success()

        if action == 'paid' and lesson_id:
            lesson = await db.fetchrow(
                '''
                UPDATE public.visit_lessons 
                SET is_cancel = FALSE, is_finish = TRUE, is_paid = TRUE
                WHERE id = $1
                RETURNING *
                ''',
                lesson_id
            )

            if not lesson:
                return self.error(message='Операция не выполнена')

            return self.success()

        return self.error()
