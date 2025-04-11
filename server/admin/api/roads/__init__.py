from sanic import Blueprint

from admin.api.roads.item import RoadView
from admin.api.roads.list import RoadsView

__all__ = ['roads_bp']

roads_bp = Blueprint('roads', url_prefix='/roads')

roads_bp.add_route(RoadsView.as_view(), '/')
roads_bp.add_route(RoadView.as_view(), '/<road_id>/')
