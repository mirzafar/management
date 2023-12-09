from sanic import Blueprint

from admin.api.analytics import power_bi_bp
from admin.api.categories import category_bp
from admin.api.chats import chats_bp
from admin.api.lessons import lessons_bp
from admin.api.main import MainView
from admin.api.roles import role_bp
from admin.api.testings import testing_bp
from admin.api.users import users_bp

main_bp = Blueprint('main', url_prefix='/')

main_bp.add_route(MainView.as_view(), '/', name='main')

api_group = Blueprint.group(
    role_bp,
    main_bp,
    category_bp,
    users_bp,
    lessons_bp,
    testing_bp,
    chats_bp,
    power_bi_bp,
    url_prefix='/api'
)
