from sanic import Blueprint

from admin.api.clients import clients_bp
from admin.api.districts import districts_bp
from admin.api.main import MainView
from admin.api.profile import profile_bp
from admin.api.regions import regions_bp
from admin.api.roles import role_bp
from admin.api.tracks import tracks_bp
from admin.api.traffics import traffics_bp
from admin.api.users import users_bp
from admin.api.visits import visits_bp

main_bp = Blueprint('main', url_prefix='/')

main_bp.add_route(MainView.as_view(), '/')

api_group = Blueprint.group(
    main_bp,
    role_bp,
    users_bp,
    clients_bp,
    visits_bp,
    profile_bp,
    tracks_bp,
    regions_bp,
    districts_bp,
    traffics_bp,
    url_prefix='/api'
)
