from sanic import Blueprint

from admin.api.reports.receipts import ReceiptsReportsView

__all__ = ['reports_bp']

reports_bp = Blueprint('reports', url_prefix='/reports')

reports_bp.add_route(ReceiptsReportsView.as_view(), '/receipts')
