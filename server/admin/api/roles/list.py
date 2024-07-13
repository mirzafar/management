from core.db import db
from core.handlers import BaseAPIView
from core.tools import set_counters
from utils.lists import ListUtils
from utils.strs import StrUtils


class RolesView(BaseAPIView):
    template_name = 'admin/roles.html'
    scopes = ['users']

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['status = 0'], []

        if query:
            cond.append('(title ILIKE {})')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        roles = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.roles
            WHERE %s
            ORDER BY id DESC
            ''' % cond,
            *cond_vars
        ))

        permissions = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.permissions
            WHERE status = 0
            '''
        ))

        return self.success(request=request, user=user, data={
            'roles': roles,
            'permissions': permissions,
        })

    async def post(self, request, user):
        title = request.json.get('title')
        description = request.json.get('description')
        permissions = ListUtils.to_list_of_strs(request.json.get('permissions'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "title: str"')

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
