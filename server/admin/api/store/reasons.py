from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreReasonsView(BaseAPIView):
    template_name = 'admin/store-reasons.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        parent_id = IntUtils.to_int(request.args.get('parent_id'))

        cond, cond_vars = ['is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 50))

        if query:
            cond.append('title ILIKE {}')
            cond_vars.append(f'%{query}%')

        if parent_id == -1:
            pass
        elif parent_id:
            cond.append('parent_id = {}')
            cond_vars.append(parent_id)
        else:
            cond.append('parent_id IS NULL')

        cond, _ = set_counters(' AND '.join(cond))

        reasons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title, description, price
            FROM store.reasons
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        return self.success(request=request, user=user, data={
            'reasons': reasons
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        description = StrUtils.to_str(request.json.get('description'))
        price = FloatUtils.to_float(request.json.get('price'))
        if not price:
            return self.error(message='Отсуствует обязательный параметры "Цена"')

        parent_id = IntUtils.to_int(request.json.get('parent_id'))

        item = await db.fetchrow(
            '''
            INSERT INTO store.reasons(title, description, price, parent_id)
            VALUES ($1, $2, $3, $4)
            RETURNING *          
            ''',
            title,
            description,
            price,
            parent_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()


class StoreReasonView(BaseAPIView):
    async def get(self, request, user, reason_id):
        reason_id = IntUtils.to_int(reason_id)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        reason = await db.fetchrow(
            '''
            SELECT id, title, description, price
            FROM store.reasons
            WHERE id = $1
            ''',
            reason_id
        ) or {}

        return self.success(data={
            'reason': dict(reason)
        })

    async def put(self, request, user, reason_id):
        reason_id = IntUtils.to_int(reason_id)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        description = StrUtils.to_str(request.json.get('description'))
        price = FloatUtils.to_float(request.json.get('price'))
        if not price:
            return self.error(message='Отсуствует обязательный параметры "Цена"')

        item = await db.fetchrow(
            '''
            UPDATE store.reasons
            SET title = $2, description = $3, price = $4
            WHERE id = $1
            RETURNING *        
            ''',
            reason_id,
            title,
            description,
            price
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, reason_id):
        reason_id = IntUtils.to_int(reason_id)
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        item = await db.fetchrow(
            '''
            UPDATE store.reasons
            SET is_active = FALSE
            WHERE id = $1 OR parent_id = $1
            RETURNING *
            ''',
            reason_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
