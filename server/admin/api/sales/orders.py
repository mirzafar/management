from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreOrdersView(BaseAPIView):
    template_name = 'admin/sales-orders.html'

    async def get(self, request, user):
        cond, cond_vars = [], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 50))

        cond, _ = set_counters(' AND '.join(cond))
        items = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                o.id,
                o.sum,
                o.discount,
                o.cashier_id,
                o.is_paid,
                o.pledge,
                o.paid_type,
                o.created_at,
                o.total_sum
            FROM sales.orders o
            %s
            ORDER BY id DESC
            %s
            ''' % (cond and 'WHERE ' + cond or '', pager.as_query()),
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM sales.orders o
            %s
            ''' % (cond and 'WHERE ' + cond or ''),
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'items': items,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        action = StrUtils.to_str(request.json.get('action'))
        if action == 'paid':
            order_id = IntUtils.to_int(request.json.get('order_id'))
            if not order_id:
                return self.error(message='Invalid order id')

            item_id = await db.fetchval(
                '''
                UPDATE sales.orders
                SET is_paid = TRUE
                WHERE id = $1
                RETURNING id
                ''',
                order_id
            )

            if not item_id:
                return self.error(message='Операция не выполнена')

            return self.success()

        return self.error()


class StoreOrdersItemView(BaseAPIView):
    template_name = 'admin/sales-orders-items.html'

    async def get(self, request, user, order_id):
        order_id = IntUtils.to_int(order_id)
        if not order_id:
            return self.error(message='Invalid order id')

        order = await db.fetchrow(
            '''
            SELECT 
                o.id,
                o.sum,
                o.discount,
                o.cashier_id,
                o.is_paid,
                o.pledge,
                o.paid_type,
                o.created_at,
                o.total_sum
            FROM sales.orders o
            WHERE o.id = $1
            ''',
            order_id
        ) or {}

        items = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT
                g.title AS good_title,
                oi.count,
                oi.sum,
                oi.price
            FROM sales.orders_item oi
            LEFT JOIN public.goods g ON oi.good_id = g.id
            WHERE oi.order_id = $1
            ''',
            order_id
        ))

        return self.success(request=request, user=user, data={
            'items': items,
            'order': dict(order)
        })
