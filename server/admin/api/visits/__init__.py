from sanic import Blueprint

from .list import VisitsView

__all__ = ['visits_bp']

visits_bp = Blueprint('visits', url_prefix='/visits')

visits_bp.add_route(VisitsView.as_view(), '/')
