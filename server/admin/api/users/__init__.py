from sanic import Blueprint

from .create import UsersCreateView
from .item import UsersItemView
from .list import UsersListView
from .template import UsersTemplateView

__all__ = ['users_bp']

users_bp = Blueprint('users')

users_bp.add_route(UsersCreateView.as_view(), '/users/create/')
users_bp.add_route(UsersTemplateView.as_view(), '/users/')
users_bp.add_route(UsersListView.as_view(), '/users/list/')
users_bp.add_route(UsersItemView.as_view(), '/users/<user_id>/')
