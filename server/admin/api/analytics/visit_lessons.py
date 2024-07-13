from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils
from utils.tools import order_date


class AnalyticsVisitLessonsView(BaseAPIView):
    template_name = 'admin/analytics-visit-lessons.html'
    scopes = ['analytics']

    async def get(self, request, user):
        start_date, stop_date = order_date(
            request.args.get('start_date'),
            request.args.get('stop_date'),
            defu='last_month'
        )

        users = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT u.id,
                   u.username,
                   u.last_name,
                   u.first_name,
                   u.username,
                   count(vr.id) FILTER ( WHERE vr.is_finish ) finish_count,
                   count(vr.id) FILTER ( WHERE vr.is_cancel ) cancel_count,
                   count(vr.id) FILTER ( WHERE vr.is_paid )   paid_count,
                   count(vr.id)                               all_count,
                   sum(vr.price) FILTER ( WHERE vr.is_paid )  sum_paid,
                   sum(vr.price)                              all_sum
            FROM public.users u
            LEFT JOIN public.visit_lessons vr ON u.id = vr.user_id AND vr.time BETWEEN $1 AND $2
            WHERE u.status = 0 AND vr.is_active
            GROUP BY u.id
            ''',
            start_date,
            stop_date
        ))

        return self.success(request=request, user=user, data={
            'users': users,
            'start_date': str(start_date.date()),
            'stop_date': str(stop_date.date()),
        })
