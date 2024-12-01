from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreGoodsView(BaseAPIView):
    template_name = 'admin/store-goods.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        cond, cond_vars = ['g.is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        if query:
            cond.append('g.title ILIKE {}')
            cond_vars.append(f'%{query}%')

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
                arrival_price,
                sale_price,
                balance,
                last_updated_at
            FROM public.goods g
            LEFT JOIN public.categories c ON c.id = g.category_id
            WHERE %s
            ORDER BY id DESC
            ''' % cond,
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
    template_name = 'admin/store-goods.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        cond, cond_vars = ['g.is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        if query:
            cond.append('(title ILIKE {})')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))
        goods = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                g.id, 
                g.title,
                CASE WHEN c.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', c.id,
                        'title', c.title
                    )
                END AS category,
                arrival_price,
                sale_price,
                balance,
                last_updated_at
            FROM public.goods g
            LEFT JOIN public.categories c ON c.id = g.category_id
            WHERE %s
            ORDER BY id DESC
            ''' % cond,
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
