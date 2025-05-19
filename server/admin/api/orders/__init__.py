from sanic import Blueprint

from admin.api.orders.item import OrderView
from admin.api.orders.list import OrdersView

__all__ = ['orders_bp']

orders_bp = Blueprint('orders', url_prefix='/orders')

orders_bp.add_route(OrdersView.as_view(), '/')
orders_bp.add_route(OrderView.as_view(), '/<order_id>/')
