from sanic import Blueprint

from admin.api.clients import clients_bp
from admin.api.companies import companies_bp
from admin.api.files import files_bp
from admin.api.goods import goods_bp
from admin.api.main import MainView
from admin.api.orders import orders_bp
from admin.api.profile import profile_bp
from admin.api.rooms import rooms_bp
from admin.api.table import table_bp
from admin.api.users import users_bp

main_bp = Blueprint('main', url_prefix='/')

main_bp.add_route(MainView.as_view(), '/')

api_group = Blueprint.group(
    main_bp,
    users_bp,
    clients_bp,
    profile_bp,
    goods_bp,
    orders_bp,
    rooms_bp,
    table_bp,
    files_bp,
    url_prefix='/api'
)
