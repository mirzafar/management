from sanic import Blueprint

from .authentication import LoginAdminView, OTPAdminView, LogoutAdminView

auth_bp = Blueprint('admin', url_prefix='/auth')

auth_bp.add_route(LoginAdminView.as_view(), '/login/')
auth_bp.add_route(LogoutAdminView.as_view(), '/logout/')
auth_bp.add_route(OTPAdminView.as_view(), '/otp/')
