from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
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

        return self.success(request=request, user=user, data={'client': dict(client)})

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
