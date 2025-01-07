from sanic import Blueprint

from .item import OrganizationView
from .list import OrganizationsView

__all__ = ['organizations_bp']

organizations_bp = Blueprint('organizations', url_prefix='/organizations')

organizations_bp.add_route(OrganizationsView.as_view(), '/')
organizations_bp.add_route(OrganizationView.as_view(), '/<organization_id>/')
