from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from utils.lists import ListUtils


class UsersTemplateView(BaseAPIView):
    template_name = 'admin/users.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        users = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                u.*, 
                r.title AS role_title
            FROM public.users u
            LEFT JOIN public.roles r ON u.role_id = r.id
            WHERE u.status > -2
            ORDER BY id DESC
            %s
            ''' % pager.as_query()
        ))

        pager.total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.users u
            WHERE u.status > -2
            '''
        ) or 0

        self.context['data'] = {
            'users': users,
            'pager': pager.dict(),
        }

        return self.render_template(request=request, user=user)
