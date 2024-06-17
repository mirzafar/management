from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class RolesItemView(BaseAPIView):
    template_name = 'admin/roles-item.html'

    async def get(self, request, user, role_id):
        role_id = IntUtils.to_int(role_id)
        if not role_id:
            return self.error(message='Отсуствует обязательный параметр "role_id"')

        item = await db.fetchrow(
            '''
            SELECT *
            FROM public.roles
            WHERE id = $1
            ''',
            role_id
        ) or {}

        permissions = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.permissions
            WHERE status = 0
            '''
        ))

        return self.success(request=request, user=user, data={'role': dict(item), 'permissions': permissions or []})

    async def put(self, request, user, role_id):
        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        permissions = ListUtils.to_list_of_strs(request.json.get('permissions'))

        role_id = IntUtils.to_int(role_id)
        if not role_id:
            return self.error(message='Отсуствует обязательный параметр "role_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.roles
            SET title = $2, description = $3, permissions = $4
            WHERE id = $1
            RETURNING *
            ''',
            role_id,
            title,
            description,
            permissions,
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, role_id):
        role_id = IntUtils.to_int(role_id)
        if not role_id:
            return self.error(message='Отсуствует обязательный параметр "role_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.roles
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            role_id,
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()
