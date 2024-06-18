from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class ClientsItemView(BaseAPIView):
    template_name = 'admin/clients-item.html'

    async def get(self, request, user, client_id):
        client_id = IntUtils.to_int(client_id)
        if not client_id:
            return self.error(message='Отсуствует обязательный параметр "client_id"')

        client = await db.fetchrow(
            '''
            SELECT *
            FROM public.clients
            WHERE id = $1
            ''',
            client_id
        ) or {}

        visits = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT v.*, 
                jsonb_build_object(
                    'id', u.id,
                    'first_name', u.first_name,
                    'last_name', u.last_name
                ) AS employee,
                jsonb_build_object(
                    'id', vs.id,
                    'title', vs.title,
                    'color', vs.color
                ) AS state
            FROM public.visits v
            LEFT JOIN public.users u ON v.user_id = u.id
            LEFT JOIN public.visit_state vs ON v.state_id = vs.id
            WHERE v.status = 0 AND v.client_id = $1
            ORDER BY v.id DESC
            ''',
            client_id
        ))

        return self.success(request=request, user=user, data={'client': dict(client), 'visits': visits})

    async def put(self, request, user, client_id):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        photo = StrUtils.to_str(request.json.get('photo'))

        client_id = IntUtils.to_int(client_id)
        if not client_id:
            return self.error(message='Отсуствует обязательный параметр "client_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.clients
            SET first_name = $2, last_name = $3, middle_name = $4, photo = $5, phone = $6
            WHERE id = $1
            RETURNING *
            ''',
            client_id,
            first_name,
            last_name,
            middle_name,
            photo,
            phone
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, client_id):
        client_id = IntUtils.to_int(client_id)
        if not client_id:
            return self.error(message='Отсуствует обязательный параметр "client_id"')

        data = await db.fetchrow(
            '''
            UPDATE public.clients
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            client_id,
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()
