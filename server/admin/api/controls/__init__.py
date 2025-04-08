from sanic import Blueprint

from admin.api.controls.companies import ControlCompaniesView

__all__ = ['controls_bp']

controls_bp = Blueprint('controls', url_prefix='/controls')

controls_bp.add_route(ControlCompaniesView.as_view(), '/companies')
