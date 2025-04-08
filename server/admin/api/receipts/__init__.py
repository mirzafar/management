from sanic import Blueprint

from admin.api.receipts.item import ReceiptView
from admin.api.receipts.list import ReceiptsView

__all__ = ['receipts_bp']

receipts_bp = Blueprint('receipts', url_prefix='/receipts')

receipts_bp.add_route(ReceiptsView.as_view(), '/')
receipts_bp.add_route(ReceiptView.as_view(), '/<receipt_id>/')
