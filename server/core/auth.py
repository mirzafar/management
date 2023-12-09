import hashlib
from functools import partial, wraps
from inspect import isawaitable
from typing import Optional

from sanic import response

__all__ = ['auth']

from core.db import db
from utils.strs import StrUtils


class Auth:
    app = None
    login_endpoint = None
    login_url = None

    def initialize(self, app):
        if self.app is not None:
            raise RuntimeError('already initialized with an application')
        self.app = app
        self.login_endpoint = app.config.get('AUTH_LOGIN_ENDPOINT', None)
        self.login_url = app.config.get('AUTH_LOGIN_URL', None)

    @classmethod
    def generate_token(cls, user_id) -> Optional[str]:
        if user_id:
            token = hashlib.md5()
            token.update(bytes(str(user_id), encoding='utf-8'))
            return token.hexdigest()
        else:
            return None

    def login_user(self, request, user):
        token = self.generate_token(user['id'])
        if token:
            await db.fetchrow(
                '''
                UPDATE public.users
                SET token = $2
                WHERE id = $1
                ''',
                user['id'],
                token
            )
            self.get_session(request)['token'] = token

    def logout_user(self, request):
        return self.get_session(request).pop('token', None)

    async def current_user(self, request):
        token = StrUtils.to_str(request.headers.get('X-API-Token'))
        if not token:
            token = self.get_session(request).get('token', None)

        if token is not None:
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
                    r.key AS role_key,
                    r.permissions AS permissions,
                    u.photo
                FROM public.users u
                LEFT JOIN public.roles r ON u.role_id = r.id
                WHERE u.token = $1
                ''',
                token
            )
            if user:
                return dict(user)

    def login_required(
        self,
        route=None,
        *,
        user_keyword='user',
        handle_no_auth=None
    ):
        if route is None:
            return partial(
                self.login_required,
                user_keyword=user_keyword,
                handle_no_auth=handle_no_auth
            )

        if handle_no_auth is not None:
            assert callable(handle_no_auth), 'handle_no_auth must be callable'

        @wraps(route)
        async def privileged(request, *args, **kwargs):
            user = await self.current_user(request)
            if isawaitable(user):
                user = await user

            if user is None:
                if handle_no_auth:
                    resp = handle_no_auth(request)
                else:
                    resp = self.handle_no_auth(request)
            else:
                if user_keyword is not None:
                    if user_keyword in kwargs:
                        raise RuntimeError(
                            'override user keyword %r in route' % user_keyword
                        )

                    kwargs[user_keyword] = user

                resp = route(request, *args, **kwargs)

            if isawaitable(resp):
                resp = await resp
            return resp

        return privileged

    @classmethod
    def get_session(cls, request):
        return request.ctx.session

    def handle_no_auth(self, request):
        u = self.login_url or request.app.url_for(self.login_endpoint)
        return response.redirect(u)


auth = Auth()
