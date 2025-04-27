from sanic import Blueprint

from admin.api.expenses.item import ExpenseView
from admin.api.expenses.list import ExpensesView

__all__ = ['expenses_bp']

expenses_bp = Blueprint('expenses', url_prefix='/expenses')

expenses_bp.add_route(ExpensesView.as_view(), '/')
expenses_bp.add_route(ExpenseView.as_view(), '/<expense_id>')
