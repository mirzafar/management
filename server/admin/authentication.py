import re

from sanic import response

from core.db import db
from core.handlers import TemplateHTTPView, auth, BaseAPIView
from core.hasher import password_to_hash
from utils.strs import StrUtils

email_regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
phone_regex = "^\\+?[1-9][0-9]{7,14}$"
password_regex = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"


class LoginAdminView(TemplateHTTPView):
    template_name = 'auth/admin/login.html'

    async def get(self, request):
        auth.logout_user(request)
        return self.render_template(request=request, user={})

    async def post(self, request):
        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))

        if not username or not password:
            return response.json({
                '_success': False,
                'message': 'Required param(s)'
            })

        user = await db.fetchrow(
            '''
            SELECT 
                u.id, 
                u.last_name,
                u.first_name,
                u.middle_name,
                u.role_id,
                u.status,
                u.password,
                u.username,
                r.title AS role_title,
                u.photo
            FROM public.users u
            LEFT JOIN public.roles r ON u.role_id = r.id
            WHERE u.username = $1 AND u.password = $2
            ''',
            username,
            password_to_hash(password=password)
        )

        if user:
            user = dict(user)
        else:
            return response.json({
                '_success': False,
                'message': 'User not found'
            })

        if user['status'] == -2:
            return response.json({
                '_success': False,
                'message': 'You do not have access'
            })

        auth.login_user(request, user)
        return response.json({
            '_success': True,
            'url': '/api/'
        })


class LogoutAdminView(BaseAPIView):
    async def get(self, request, user):
        auth.logout_user(request)
        return response.redirect('/api/')
