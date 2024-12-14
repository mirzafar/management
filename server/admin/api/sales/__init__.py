from sanic import Blueprint

from admin.api.sales.categories import SalesCategoriesView
from admin.api.sales.goods import SalesGoodsView

__all__ = ['sales_bp']

from admin.api.sales.index import StoreIndexView

sales_bp = Blueprint('sales', url_prefix='/sales')

sales_bp.add_route(SalesGoodsView.as_view(), '/goods/')
sales_bp.add_route(SalesCategoriesView.as_view(), '/categories/')
sales_bp.add_route(StoreIndexView.as_view(), '/index/')
