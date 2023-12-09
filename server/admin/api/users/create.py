import re

from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils

email_regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')


class UsersCreateView(BaseAPIView):
    template_name = 'admin/users-create.html'

    async def get(self, request, user):
        roles = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.roles
            WHERE status >= 0
            '''
        ))

        self.context['data'] = {
            'roles': roles
        }

        return self.render_template(request=request, user=user)
