import hashlib
from functools import partial, wraps
from inspect import isawaitable
from typing import Optional

import ujson
from sanic import response

from core.cache import cache
from core.db import db
from local_settings import settings

__all__ = ['auth']


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

    @classmethod
    def logout(cls, request):
        request.ctx.session['_delete'] = True

    @classmethod
    async def get_user(cls, user_id: int) -> Optional[dict]:
        if not user_id:
            return None

        user = await cache.get(f'user:{user_id}')
        if user:
            return ujson.loads(user)

        user = await db.fetchrow(
            '''
            SELECT u.id,
                   u.last_name,
                   u.first_name,
                   u.middle_name,
                   u.status,
                   u.password,
                   u.username,
                   u.photo,
                   r.permissions
            FROM public.users u
                     LEFT JOIN public.roles r ON u.role_id = r.id
            WHERE u.id = $1
            ''',
            user_id
        ) or {}
        if user:
            await cache.setex(f'user:{user_id}', 60 * 60 * 5, ujson.dumps(dict(user)))
        return dict(user)

    @classmethod
    async def current_user(cls, request) -> Optional[dict]:
        token = request.headers.get('X-API-Token') or request.args.get('token') or request.ctx.session.get('token')
        if not token:
            return None

        session = ujson.loads(await cache.get(f'session:{token}') or '{}')
        if not session:
            return None

        await cache.expire(f'session:{token}', 60 * 60 * 1)
        return await cls.get_user(session['user_id'])

    def login_required(
        self,
        route=None,
        *,
        user_keyword: str = 'user',
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
                user = user

            if user:
                if user_keyword is not None:
                    if user_keyword in kwargs:
                        raise RuntimeError(
                            'override user keyword %r in route' % user_keyword
                        )

                    kwargs[user_keyword] = dict(user)

                resp = route(request, *args, **kwargs)
            else:
                if handle_no_auth:
                    resp = handle_no_auth(request)
                else:
                    resp = self.handle_no_auth(request)

            if isawaitable(resp):
                resp = await resp
            return resp

        return privileged

    @classmethod
    def get_session(cls, request):
        return request.ctx.session

    def handle_no_auth(self, request):
        if settings['response_type'] in ['json']:
            return response.json(
                headers={
                    'X-authentication': 'expired_token'
                },
                body={
                    'success': False,
                    'error_reason': 'expired_token'
                },
                status=401
            )
        else:
            return response.redirect(self.login_url or request.app.url_for(self.login_endpoint))


auth = Auth()
