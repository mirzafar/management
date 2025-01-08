from sanic import Blueprint

from .authentication import LoginAdminView
from .authentication import LogoutAdminView

auth_bp = Blueprint('admin', url_prefix='/auth')

auth_bp.add_route(LoginAdminView.as_view(), '/login/')
auth_bp.add_route(LogoutAdminView.as_view(), '/logout/')
