from sanic import Blueprint

from admin.api.analytics import power_bi_bp
from admin.api.categories import category_bp
from admin.api.chats import chats_bp
from admin.api.districts import districts_bp
from admin.api.lessons import lessons_bp
from admin.api.main import MainView
from admin.api.organizations import organizations_bp
from admin.api.profile import profile_bp
from admin.api.regions import regions_bp
from admin.api.roles import role_bp
from admin.api.sales import sales_bp
from admin.api.testings import testing_bp
from admin.api.tracks import tracks_bp
from admin.api.users import users_bp

main_bp = Blueprint('main', url_prefix='/')

main_bp.add_route(MainView.as_view(), '/', name='main')

api_group = Blueprint.group(
    main_bp,
    users_bp,
    tracks_bp,
    regions_bp,
    districts_bp,
    url_prefix='/api'
)
