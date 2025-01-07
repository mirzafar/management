from sanic import Blueprint

from .item import EmployeeView
from .list import EmployeesView

__all__ = ['employees_bp']

employees_bp = Blueprint('employees', url_prefix='/employees')

employees_bp.add_route(EmployeesView.as_view(), '/')
employees_bp.add_route(EmployeeView.as_view(), '/<employee_id>/')
