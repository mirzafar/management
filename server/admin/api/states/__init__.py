from sanic import Blueprint

from admin.api.states.item import StateView
from admin.api.states.list import StatesView

__all__ = ['states_bp']

states_bp = Blueprint('states', url_prefix='/states')

states_bp.add_route(StatesView.as_view(), '/')
states_bp.add_route(StateView.as_view(), '/<state_id>/')
