from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.bools import BoolUtils
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

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        cond, cond_vars = ['v.is_active', 'v.client_id = {}'], [client_id]

        is_paid = BoolUtils.to_bool(request.args.get('is_paid'))
        if is_paid is None:
            pass
        else:
            cond.append('v.is_paid = {}')
            cond_vars.append(is_paid)

        cond, _ = set_counters(' AND '.join(cond))
        visits = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                v.id, 
                v.description, 
                CASE WHEN g.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', g.id,
                        'title', g.title
                    )
                END AS good,
                v.is_our,
                CASE WHEN r.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', r.id,
                        'title', r.title
                    )
                END AS reason,
                v.count,
                v.sum,
                v.created_at,
                v.is_paid
            FROM store.visits v
            LEFT JOIN public.goods g ON g.id = v.good_id
            LEFT JOIN store.reasons r ON r.id = v.reason_id
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM store.visits v
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'client': dict(client),
            'visits': visits,
            'pager': pager.dict()
        })

    async def put(self, request, user, client_id):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        photo = StrUtils.to_str(request.json.get('photo'))
        address = StrUtils.to_str(request.json.get('address'))

        client_id = IntUtils.to_int(client_id)
        if not client_id:
            return self.error(message='Отсуствует обязательный параметр "client_id"')

        if not first_name:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        if not last_name:
            return self.error(message='Отсуствует обязательный параметры "Фамилия"')

        data = await db.fetchrow(
            '''
            UPDATE public.clients
            SET first_name = $2, last_name = $3, middle_name = $4, photo = $5, phone = $6, address = $7
            WHERE id = $1
            RETURNING *
            ''',
            client_id,
            first_name,
            last_name,
            middle_name,
            photo,
            phone,
            address
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
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *
            ''',
            client_id,
        )

        if not data:
            return self.error(message='Операция не выполнена')

        return self.success()
