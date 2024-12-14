from core.db import db
from core.handlers import BaseAPIView
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class SalesGoodsView(BaseAPIView):

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        category_id = IntUtils.to_int(request.args.get('category_id'))
        cond, cond_vars = [], []

        if query:
            cond.append('g.title ILIKE {}')
            cond_vars.append(f'%{query}%')

        if category_id:
            cond.append('g.category_id = {}')
            cond_vars.append(category_id)

        if cond:
            cond.append('g.is_active')
        else:
            return self.success(data={
                'items': []
            })

        cond, _ = set_counters(' AND '.join(cond))
        goods = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                g.id, 
                g.title,
                g.last_arrival_price,
                g.price,
                g.balance,
                g.last_updated_at,
                g.last_arrival_price
            FROM public.goods g
            WHERE %s
            ORDER BY id DESC
            LIMIT %s
            ''' % (cond, IntUtils.to_int(request.args.get('limit'), default=100)),
            *cond_vars
        ))

        return self.success(data={
            'items': goods
        })
