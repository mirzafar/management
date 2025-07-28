from sanic import Blueprint

from admin.api.chats.item import ChatView
from admin.api.chats.list import ChatsView

__all__ = ['chats_bp']

chats_bp = Blueprint('chats', url_prefix='/chats')

chats_bp.add_route(ChatsView.as_view(), '/')
chats_bp.add_route(ChatView.as_view(), '/<chat_id>/')
