from sanic import Blueprint

from .authentication import LoginAdminView
from .authentication import LogoutAdminView

admin_bp = Blueprint('admin', url_prefix='/admin')

admin_bp.add_route(LoginAdminView.as_view(), '/login/')
admin_bp.add_route(LogoutAdminView.as_view(), '/logout/')
