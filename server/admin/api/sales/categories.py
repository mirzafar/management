from core.db import db
from core.handlers import BaseAPIView
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class SalesCategoriesView(BaseAPIView):

    async def get(self, request, user):
        parent_id = IntUtils.to_int(request.args.get('parent_id'))
        query = StrUtils.to_str(request.args.get('query'))
        cond, cond_vars = ['is_active'], []

        if parent_id == -1:
            cond.append('parent_id IS NULL')

        elif parent_id:
            cond.append('parent_id = {}')
            cond_vars.append(parent_id)

        if query:
            cond.append('title ILIKE {}')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))
        categories = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title, unit, description
            FROM public.categories
            WHERE %s
            ORDER BY id
            ''' % cond,
            *cond_vars
        ))

        return self.success(request=request, user=user, data={'items': categories})
