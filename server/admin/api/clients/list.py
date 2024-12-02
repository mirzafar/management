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
        pager.set_limit(request.args.get('limit', 20))

        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['cu.is_active'], []

        if query:
            cond.append('(cu.first_name ILIKE {same} OR cu.last_name ILIKE {same} OR cu.phone ILIKE {same})')
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

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM public.clients cu
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'clients': clients,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        address = StrUtils.to_str(request.json.get('address'))

        if not first_name:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        if not last_name:
            return self.error(message='Отсуствует обязательный параметры "Фамилия"')

        user = await db.fetchrow(
            '''
            INSERT INTO public.clients
            (last_name, first_name, middle_name, phone, address)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            ''',
            last_name,
            first_name,
            middle_name,
            phone,
            address
        )

        if not user:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'employee': dict(user)
        })
