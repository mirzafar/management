from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class UsersListView(BaseAPIView):
    template_name = 'admin/users.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        query = StrUtils.to_str(request.args.get('query'))
        status = IntUtils.to_int(request.args.get('status'))

        cond, cond_vars = [], []

        if query:
            cond.append('(u.first_name ILIKE {} OR u.last_name ILIKE {})')
            cond_vars.append(f'%{query}%')
            cond_vars.append(f'%{query}%')

        if status is not None:
            cond.append('u.status = {}')
            cond_vars.append(status)
        else:
            cond.append('u.status = {}')
            cond_vars.append(0)

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

        roles = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.roles
            WHERE status >= 0
            '''
        ))

        pager.total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.users u
            WHERE u.status > -2
            '''
        ) or 0

        return self.success(request=request, user=user, data={
            '_success': True,
            'users': users,
            'pager': pager.dict(),
            'user': dict(user),
            'roles': roles
        })
