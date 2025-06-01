from sanic import Blueprint

from admin.api.rooms.item import RoomView
from admin.api.rooms.list import RoomsView

__all__ = ['rooms_bp']

rooms_bp = Blueprint('rooms', url_prefix='/rooms')

rooms_bp.add_route(RoomsView.as_view(), '/')
rooms_bp.add_route(RoomView.as_view(), '/<room_id>/')
