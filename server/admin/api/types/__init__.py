from sanic import Blueprint

from admin.api.types.item import TypeView
from admin.api.types.list import TypesView

__all__ = ['types_bp']

types_bp = Blueprint('types', url_prefix='/types')

types_bp.add_route(TypesView.as_view(), '/')
types_bp.add_route(TypeView.as_view(), '/<type_id>/')
