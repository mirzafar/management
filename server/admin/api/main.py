from datetime import datetime

from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils


class MainView(BaseAPIView):
    template_name = 'admin/index.html'

    async def get(self, request, user):
        now = datetime.now()
        lessons = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT  vl.*,
                    json_build_object(
                        'id', c.id,
                        'first_name', c.first_name,
                        'last_name', c.last_name
                    ) AS customer,
                    vr.title AS reason
            FROM public.visit_lessons vl
            LEFT JOIN public.visits v ON vl.visit_id = v.id 
            LEFT JOIN public.clients c ON v.client_id = c.id
            LEFT JOIN public.visit_reasons vr ON v.reason_id = vr.id
            WHERE vl.user_id = $1 AND vl.date_key = $2 AND vl.is_active AND vl.is_cancel = FALSE
            ''',
            user['id'],
            str(now.date())
        ))
        return self.success(request=request, user=user, data={
            'lessons': lessons,
            'date_key': str(now.date())
        })
