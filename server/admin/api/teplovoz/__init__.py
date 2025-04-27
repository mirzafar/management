from sanic import Blueprint

from admin.api.teplovoz.item import TeplovozItemView
from admin.api.teplovoz.list import TeplovozView

__all__ = ['teplovoz_bp']

teplovoz_bp = Blueprint('teplovoz', url_prefix='/teplovoz')

teplovoz_bp.add_route(TeplovozView.as_view(), '/')
teplovoz_bp.add_route(TeplovozItemView.as_view(), '/<teplovoz_id>/')
