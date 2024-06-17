from sanic import Blueprint

from .list import ClientsView
from .item import ClientsItemView

__all__ = ['clients_bp']

clients_bp = Blueprint('clients', url_prefix='/clients')

clients_bp.add_route(ClientsView.as_view(), '/')
clients_bp.add_route(ClientsItemView.as_view(), '/<client_id>/')
