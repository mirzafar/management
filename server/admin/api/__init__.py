from sanic import Blueprint

from admin.api.analytics import analytics_bp
from admin.api.clients import clients_bp
from admin.api.companies import companies_bp
from admin.api.main import MainView
from admin.api.profile import profile_bp
from admin.api.roles import role_bp
from admin.api.sales import sales_bp
from admin.api.store import store_bp
from admin.api.users import users_bp

main_bp = Blueprint('main', url_prefix='/')

main_bp.add_route(MainView.as_view(), '/')

api_group = Blueprint.group(
    main_bp,
    role_bp,
    store_bp,
    users_bp,
    clients_bp,
    profile_bp,
    sales_bp,
    companies_bp,
    url_prefix='/api'
)
