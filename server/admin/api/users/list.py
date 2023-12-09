from sanic import response

from core.db import db
from core.encoder import encoder
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.lists import ListUtils
from utils.strs import StrUtils


class UsersListView(BaseAPIView):
    template_name = 'admin/users.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['u.status > {}'], [-2]

        if query:
            cond.append('u.first_name ILIKE {} OR u.last_name ILIKE {}')
            cond_vars.append(f'%{query}%')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        users = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                u.*, 
                r.title AS role_title
            FROM public.users u
            LEFT JOIN public.roles r ON u.role_id = r.id
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        pager.total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.users u
            WHERE u.status > -2
            '''
        ) or 0

        self.context = {
            '_success': True,
            'users': users,
            'pager': pager.dict(),
            'user': dict(user),
        }

        return response.json(self.context, dumps=encoder.encode)
