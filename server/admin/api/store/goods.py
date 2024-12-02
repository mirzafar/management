from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreGoodsView(BaseAPIView):
    template_name = 'admin/store-goods.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        category_id = IntUtils.to_int(request.args.get('category_id'))
        cond, cond_vars = ['g.is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        if query:
            cond.append('g.title ILIKE {}')
            cond_vars.append(f'%{query}%')

        if category_id:
            cond.append('g.category_id = {}')
            cond_vars.append(category_id)

        cond, _ = set_counters(' AND '.join(cond))

        goods = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                g.id, 
                g.title,
                CASE WHEN c.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', c.id,
                        'title', c.title,
                        'unit', c.unit
                    )
                END AS category,
                last_arrival_price,
                sale_price,
                price,
                balance,
                last_updated_at,
                last_arrival_price
            FROM public.goods g
            LEFT JOIN public.categories c ON c.id = g.category_id
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM public.goods g
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'goods': goods,
            'pager': pager.dict()
        })


class StoreGoodView(BaseAPIView):
    async def get(self, request, user, good_id):
        good_id = IntUtils.to_int(good_id)
        if not good_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        good = await db.fetchrow(
            '''
            SELECT 
                g.id, 
                g.title,
                CASE WHEN c.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', c.id,
                        'title', c.title,
                        'unit', c.unit
                    )
                END AS category,
                last_arrival_price,
                price,
                balance,
                last_updated_at
            FROM public.goods g
            LEFT JOIN public.categories c ON c.id = g.category_id
            WHERE g.id = $1
            ''',
            good_id
        ) or {}

        return self.success(request=request, user=user, data={
            'good': dict(good)
        })

    async def put(self, request, user, good_id):
        good_id = IntUtils.to_int(good_id)
        if not good_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        price = FloatUtils.to_float(request.json.get('price'))
        balance = FloatUtils.to_float(request.json.get('balance'), default=0)

        if not price:
            return self.error(message='Отсуствует обязательный параметры "Цена"')

        item = await db.fetchrow(
            '''
            UPDATE public.goods
            SET price = $2, balance = $3
            WHERE id = $1
            RETURNING *
            ''',
            good_id,
            price,
            balance
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, good_id):
        good_id = IntUtils.to_int(good_id)
        if not good_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        item = await db.fetchrow(
            '''
            UPDATE public.goods
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *          
            ''',
            good_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
