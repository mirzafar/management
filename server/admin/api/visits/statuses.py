from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils


class VisitsStatesView(BaseAPIView):
    template_name = 'admin/visits-states.html'

    async def get(self, request, user):
        states = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.visit_state
            WHERE status = 0
            ORDER BY id DESC
            '''
        ))

        return self.success(request=request, user=user, data={
            'states': states
        })
