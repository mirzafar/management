from sanic import Blueprint

from admin.api.analytics.visit_reasons import AnalyticsVisitReasonsView

__all__ = ['analytics_bp']

analytics_bp = Blueprint('analytics', url_prefix='/analytics')

analytics_bp.add_route(AnalyticsVisitReasonsView.as_view(), '/visits-reasons/')
