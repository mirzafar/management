from sanic import response
from sanic_openapi import doc

from core.db import db
from core.handlers import TemplateHTTPView, auth, BaseAPIView
from core.hasher import password_to_hash
from core.session import session
from models import UsersLoginModels
from settings import settings
from utils.strs import StrUtils


class LoginAdminView(TemplateHTTPView):
    template_name = 'auth/login.html'

    async def get(self, request):
        await auth.logout(request)
        return self.success(request=request)

    @doc.consumes(UsersLoginModels, location='body')
    async def post(self, request):
        if not request.json:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр(ы)'
            })

        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))

        if not username:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр "username: str"'
            })

        if not password:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр "password: str"'
            })

        user = await db.fetchrow(
            '''
            SELECT *
            FROM public.users u
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
                'message': 'Пользователь не найден(-o, -а) в системе'
            })

        if user['status'] == -1:
            return response.json({
                '_success': False,
                'message': 'Пользователь заблокирован(-о, -а) в системе'
            })

        elif user['status'] == -2:
            return response.json({
                '_success': False,
                'message': 'Пользователь удален(-о, -а) из системы'
            })

        token = await session.create_session(request, user['id'])
        await auth.login(request, user, token)

        return response.json({
            '_success': True,
            'url': '/api/',
            'token': token,
            'user_id': user['id'],
        })


class LogoutAdminView(BaseAPIView):
    async def get(self, request, user):
        await auth.logout(request)
        return response.redirect('/')


class RegisterAdminView(TemplateHTTPView):
    template_name = 'auth/register.html'

    async def get(self, request):
        await auth.logout(request)
        return self.success(request=request)

    async def post(self, request):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))
        reply_password = StrUtils.to_str(request.json.get('reply_password'))

        if not last_name:
            return self.error(message='Введите фамилию')

        if not first_name:
            return self.error(message='Введите имя')

        if username:
            duplicate = await db.fetchrow(
                '''
                SELECT *
                FROM public.users
                WHERE username = $1
                ''',
                username
            )
            if duplicate:
                return self.error(
                    message='Пользователь с этими значениями уже существует. Дубликат не может быть создан'
                )

        else:
            return self.error(message='Введите имя пользователя')

        if not password:
            return self.error(message='Введите пароль')

        if not password == reply_password:
            return self.error(message='Пароли не совпадают')

        user = await db.fetchrow(
            '''
            INSERT INTO public.users
            (last_name, first_name, middle_name, password, username, role_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
            ''',
            last_name,
            first_name,
            middle_name,
            password_to_hash(password),
            username,
            settings.get('customer_role_id', None)
        )

        if not user:
            return self.error(message='Операция не выполнена')

        token = await session.create_session(request, user['id'])
        await auth.login(request, user, token)

        return self.success(
            data={
                'user': dict(user),
                'url': '/api/',
                'token': token,
                'user_id': user['id'],
            }
        )
