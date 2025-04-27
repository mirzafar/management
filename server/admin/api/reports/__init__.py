from sanic import Blueprint

from admin.api.reports.list import ReportsView
from admin.api.reports.receipts import ReceiptsReportsView
from admin.api.reports.record_acceptance import RecordAcceptanceReportsView
from admin.api.reports.roads import RoadsReportsView
from admin.api.reports.service_reference import ServicesReferenceReportsView
from admin.api.reports.stayed import StayedReportsView

__all__ = ['reports_bp']

reports_bp = Blueprint('reports', url_prefix='/reports')

reports_bp.add_route(ReceiptsReportsView.as_view(), '/receipts')
reports_bp.add_route(StayedReportsView.as_view(), '/stayed')
reports_bp.add_route(ServicesReferenceReportsView.as_view(), '/services-reference')
reports_bp.add_route(RecordAcceptanceReportsView.as_view(), '/record-acceptance')
reports_bp.add_route(RoadsReportsView.as_view(), '/roads')
reports_bp.add_route(ReportsView.as_view(), '/')
