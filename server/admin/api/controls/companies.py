from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.ints import IntUtils
from utils.strs import StrUtils


class ControlCompaniesView(BaseAPIView):
    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))
        offset = IntUtils.to_int(request.args.get('offset')) or pager.offset

        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.companies.find(filters).skip(offset) \
            .limit(pager.limit) \
            .sort('_id', -1) \
            .to_list(length=None)

        return self.success(data={
            'companies': items
        })
