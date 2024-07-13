from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils
from utils.tools import order_date


class VisitsView(BaseAPIView):
    template_name = 'admin/visits.html'
    scopes = ['visit-list']

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        query = StrUtils.to_str(request.args.get('query'))

        start_date, stop_date = order_date(
            request.args.get('start_date'),
            request.args.get('stop_date'),
            defu='last_month'
        )

        cond, cond_vars = ['v.created_at BETWEEN {} AND {}'], [start_date, stop_date]

        if query:
            cond.append('(cu.first_name ILIKE {} OR cu.last_name ILIKE {})')
            cond_vars.append(f'%{query}%')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        visits = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT v.*, 
                jsonb_build_object(
                    'id', u.id,
                    'first_name', u.first_name,
                    'last_name', u.last_name
                ) AS author,
                jsonb_build_object(
                    'id', cu.id,
                    'first_name', cu.first_name,
                    'last_name', cu.last_name,
                    'photo', cu.photo
                ) AS customer,
                vr.title AS reason
            FROM public.visits v
            LEFT JOIN public.users u ON v.author_id = u.id
            LEFT JOIN public.clients cu ON v.client_id = cu.id
            LEFT JOIN public.visit_reasons vr ON v.reason_id = vr.id
            WHERE v.is_active AND %s
            ORDER BY v.id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM public.visits v
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'visits': visits,
            'pager': pager.dict(),
            'start_date': str(start_date.date()),
            'stop_date': str(stop_date.date()),

        })

    async def post(self, request, user):
        reason_id = IntUtils.to_int(request.json.get('reason_id'))
        description = StrUtils.to_str(request.json.get('description'))
        client_id = IntUtils.to_int(request.json.get('client_id'))
        count_lesson = IntUtils.to_int(request.json.get('count_lesson'), default=1)
        price = FloatUtils.to_float(request.json.get('price'), default=0)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметры "reason_id: int"')

        item = await db.fetchrow(
            '''
            INSERT INTO public.visits
            (reason_id, description, client_id, count_lesson, author_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            ''',
            reason_id,
            description,
            client_id,
            count_lesson,
            user['id']
        )

        if not item:
            return self.error(message='Операция не выполнена')

        await db.execute(
            '''
            UPDATE public.visit_reasons
            SET count = count + 1
            WHERE id = $1
            ''',
            reason_id
        )

        if count_lesson and count_lesson > 0:
            await db.executemany(
                '''
                INSERT INTO public.visit_lessons(user_id, visit_id, price)
                VALUES ($1, $2, $3)
                ON CONFLICT DO NOTHING 
                ''',
                [(user['id'], item['id'], price) for _ in range(1, count_lesson + 1)]
            )

        return self.success()
