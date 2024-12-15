from sanic import Blueprint

from admin.api.sales.categories import SalesCategoriesView
from admin.api.sales.goods import SalesGoodsView
from admin.api.sales.index import StoreIndexView
from admin.api.sales.orders import StoreOrdersView, StoreOrdersItemView

__all__ = ['sales_bp']

sales_bp = Blueprint('sales', url_prefix='/sales')

sales_bp.add_route(SalesGoodsView.as_view(), '/goods/')
sales_bp.add_route(SalesCategoriesView.as_view(), '/categories/')
sales_bp.add_route(StoreIndexView.as_view(), '/index/')
sales_bp.add_route(StoreOrdersView.as_view(), '/orders/')
sales_bp.add_route(StoreOrdersItemView.as_view(), '/orders/<order_id>/items/')
