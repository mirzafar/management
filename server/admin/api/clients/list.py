from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.lists import ListUtils
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class ClientsView(BaseAPIView):
    template_name = 'admin/clients.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))

        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['cu.status = 0'], []

        if query:
            cond.append('(cu.first_name ILIKE {} OR cu.last_name ILIKE {})')
            cond_vars.append(f'%{query}%')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        clients = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT cu.*
            FROM public.clients cu
            WHERE %s
            ORDER BY cu.id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.clients cu
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0

        return self.success(request=request, user=user, data={
            'clients': clients,
            'total': total
        })

    async def post(self, request, user):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        photo = StrUtils.to_str(request.json.get('photo'))

        if not first_name or not last_name:
            return self.error(message='Отсуствует обязательный параметры "first_name: str, last_name: str"')

        user = await db.fetchrow(
            '''
            INSERT INTO public.clients
            (last_name, first_name, middle_name, photo, phone)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            ''',
            last_name,
            first_name,
            middle_name,
            photo,
            phone
        )

        if not user:
            return self.error(message='Операция не выполнена')

        return self.success()
