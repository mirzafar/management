from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.lists import ListUtils
from utils.tools import order_date


class MainView(BaseAPIView):
    template_name = 'admin/index.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        start_date, stop_date = order_date(
            request.args.get('start_date'),
            request.args.get('stop_date'),
            defu='last_day'
        )

        lessons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT  vl.id, 
                    vl.time, 
                    vl.room, 
                    is_cancel, 
                    is_finish, 
                    is_paid,
                    price,
                    vl.visit_id,
                    jsonb_build_object(
                        'id', c.id,
                        'first_name', c.first_name,
                        'last_name', c.last_name,
                        'photo', c.photo
                    ) AS client
            FROM public.visit_lessons vl
            LEFT JOIN public.visits v ON vl.visit_id = v.id
            LEFT JOIN public.clients c ON v.client_id = c.id
            WHERE vl.is_active AND vl.time BETWEEN $1 AND $2 AND vl.user_id = $3
            ORDER BY vl.time DESC, vl.id DESC
            %s
            ''' % pager.as_query(),
            start_date,
            stop_date,
            user['id']
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM public.visit_lessons vl
            WHERE vl.is_active AND vl.time BETWEEN $1 AND $2 AND vl.user_id = $3
            ''',
            start_date,
            stop_date,
            user['id']
        ) or 0)

        return self.success(request=request, user=user, data={
            'lessons': lessons,
            'pager': pager.dict(),
            'start_date': str(start_date.date()),
            'stop_date': str(stop_date.date()),
        })
