from sanic import Blueprint

from admin.api.companies.item import CompanyView
from admin.api.companies.list import CompaniesView

__all__ = ['companies_bp']

companies_bp = Blueprint('companies', url_prefix='/companies')

companies_bp.add_route(CompaniesView.as_view(), '/')
companies_bp.add_route(CompanyView.as_view(), '/<company_id>/')
