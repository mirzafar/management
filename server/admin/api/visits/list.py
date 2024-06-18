from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class VisitsView(BaseAPIView):
    template_name = 'admin/clients-visits.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))

        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['v.status = 0'], []

        if query:
            cond.append('(cu.first_name ILIKE {} OR cu.last_name ILIKE {})')
            cond_vars.append(f'%{query}%')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        visits = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT v.*
            FROM public.visits v
            WHERE %s
            ORDER BY v.id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.visits v
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0

        return self.success(request=request, user=user, data={
            'visits': visits,
            'total': total
        })

    async def post(self, request, user):
        reason = StrUtils.to_str(request.json.get('reason'))
        description = StrUtils.to_str(request.json.get('description'))
        client_id = IntUtils.to_int(request.json.get('client_id'))
        user_id = IntUtils.to_int(request.json.get('user_id'))
        count_lesson = IntUtils.to_int(request.json.get('count_lesson   '))

        if not reason:
            return self.error(message='Отсуствует обязательный параметры "reason: str"')

        item = await db.fetchrow(
            '''
            INSERT INTO public.visits
            (reason, description, client_id, user_id, count_lesson)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            ''',
            reason,
            description,
            client_id,
            user_id,
            count_lesson
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
