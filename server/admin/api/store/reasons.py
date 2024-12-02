from core.db import db
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreReasonsView(BaseAPIView):
    template_name = 'admin/store-reasons.html'

    async def get(self, request, user):
        reasons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title, description, price
            FROM store.reasons
            WHERE is_active
            ORDER BY id DESC
            '''
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

        item = await db.fetchrow(
            '''
            INSERT INTO store.reasons(title, description, price)
            VALUES ($1, $2, $3)
            RETURNING *          
            ''',
            title,
            description,
            price
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
            WHERE id = $1
            RETURNING *        
            ''',
            reason_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
