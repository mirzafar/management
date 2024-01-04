from sanic import Blueprint

from .item import UsersItemView
from .list import UsersListView

__all__ = ['users_bp']

users_bp = Blueprint('users')

users_bp.add_route(UsersListView.as_view(), '/users/')
users_bp.add_route(UsersItemView.as_view(), '/users/<user_id>/')
