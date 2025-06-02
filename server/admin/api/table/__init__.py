from sanic import Blueprint

from admin.api.table.list import TableView

__all__ = ['table_bp']

table_bp = Blueprint('table', url_prefix='/table')

table_bp.add_route(TableView.as_view(), '/')
