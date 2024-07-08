from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils
from utils.tools import order_date


class AnalyticsVisitReasonsView(BaseAPIView):
    template_name = 'admin/analytics-visit-reasons.html'

    async def get(self, request, user):
        start_date, stop_date = order_date(
            request.args.get('start_date'),
            request.args.get('stop_date'),
            defu='last_month'
        )

        reasons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT vr.id, vr.title, vr.count AS all_count, COUNT(v.id)
            FROM public.visit_reasons vr
            LEFT JOIN visits v ON vr.id = v.reason_id
            WHERE v.created_at BETWEEN $1 AND $2
            GROUP BY vr.id
            ''',
            start_date,
            stop_date
        ))

        return self.success(request=request, user=user, data={
            'reasons': reasons,
            'start_date': str(start_date.date()),
            'stop_date': str(stop_date.date()),
        })
