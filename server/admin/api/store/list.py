from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.floats import FloatUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class RolesView(BaseAPIView):
    template_name = 'admin/store.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        cond, cond_vars = ['g.is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        if query:
            cond.append('(title ILIKE {})')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))
        goods = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.store g
            WHERE %s
            ORDER BY id DESC
            ''' % cond,
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM public.store g
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'store': goods,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название "')

        unit = StrUtils.to_str(request.json.get('unit'))
        if not unit:
            return self.error(message='Отсуствует обязательный параметры "Eдиница измерений"')

        arrival_price = FloatUtils.to_float(request.json.get('arrival_price'))

        permissions = ListUtils.to_list_of_strs(request.json.get('permissions'))

        item = await db.fetchrow(
            '''
            INSERT INTO public.roles(title, description, permissions)
            VALUES ($1, $2, $3)
            RETURNING *          
            ''',
            title,
            description,
            permissions
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
