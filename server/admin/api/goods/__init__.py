from sanic import Blueprint

from admin.api.goods.item import GoodView
from admin.api.goods.list import GoodsView

__all__ = ['goods_bp']

goods_bp = Blueprint('goods', url_prefix='/goods')

goods_bp.add_route(GoodsView.as_view(), '/')
goods_bp.add_route(GoodView.as_view(), '/<good_id>/')
