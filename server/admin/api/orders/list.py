from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.ints import IntUtils
from datetime import datetime

class OrdersView(BaseAPIView):
    template_name = 'admin/orders.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 100))
        offset = IntUtils.to_int(request.args.get('offset')) or pager.offset

        filters = {
            # 'is_active': True
        }

        items = await mongo.orders.find(filters).skip(offset) \
            .limit(pager.limit) \
            .sort('_id', -1) \
            .to_list(length=None)

        return self.success(request=request, user=user, data={
            'orders': items,
            'pager': pager.dict()
        })
