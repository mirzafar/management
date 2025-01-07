from sanic import Blueprint

from admin.api.organizations import organizations_bp
from admin.api.users import employees_bp

main_bp = Blueprint('main', url_prefix='/')

api_group = Blueprint.group(
    organizations_bp,
    employees_bp,
    url_prefix='/api'
)
