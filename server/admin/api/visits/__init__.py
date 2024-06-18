from sanic import Blueprint

from .item import VisitsItemView
from .lessons.list import VisitsLessonsView
from .list import VisitsView
from .statuses import VisitsStatesView

__all__ = ['visits_bp']

visits_bp = Blueprint('visits', url_prefix='/visits')

visits_bp.add_route(VisitsView.as_view(), '/')
visits_bp.add_route(VisitsStatesView.as_view(), '/states')
visits_bp.add_route(VisitsItemView.as_view(), '/<visit_id>/')
visits_bp.add_route(VisitsLessonsView.as_view(), '/<visit_id>/lessons/')
