from datetime import datetime

from sanic import response

from core.db import db
from core.handlers import BaseAPIView
from core.hasher import password_to_hash
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class UsersItemView(BaseAPIView):
    template_name = 'admin/users-item.html'

    async def get(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): user_id'
            })

        customer = await db.fetchrow(
            '''
            SELECT *
            FROM public.users
            WHERE id = $1
            ''',
            user_id
        )

        roles = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.roles
            WHERE status >= 0
            '''
        ))

        self.context['data'] = {
            'user': dict(customer or {}),
            'roles': roles,
        }

        return self.render_template(request=request, user=user)

    async def post(self, request, user, user_id):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        birthday = StrUtils.to_str(request.json.get('birthday'))
        username = StrUtils.to_str(request.json.get('username'))
        role_id = IntUtils.to_int(request.json.get('role_id'))
        password = StrUtils.to_str(request.json.get('password'))
        reply_password = StrUtils.to_str(request.json.get('reply_password'))
        photo = StrUtils.to_str(request.json.get('photo'))
        status = IntUtils.to_int(request.json.get('status')) or 0

        if not first_name or not last_name:
            return response.json({
                '_success': False,
                'message': 'Required param(s): first_name or last_name'
            })

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
                return response.json({
                    '_success': False,
                    'message': 'Duplicate: username'
                })

        else:
            return response.json({
                '_success': False,
                'message': 'Required param(s): username'
            })

        if password:
            if password == reply_password:
                password = password_to_hash(password)
            else:
                return response.json({
                    '_success': False,
                    'message': 'Password does not match'
                })

        else:
            return response.json({
                '_success': False,
                'message': 'Required param(s): password'
            })

        if not role_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): role_id'
            })

        user = await db.fetchrow(
            '''
            INSERT INTO public.users
            (last_name, first_name, middle_name, role_id, password, username, photo, birthday, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            ''',
            last_name,
            first_name,
            middle_name,
            role_id,
            password,
            username,
            photo,
            datetime.strptime(birthday, '%Y-%m-%d') if birthday else None,
            status,
        )

        if not user:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True
        })

    async def put(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): user_id'
            })

        customer = await db.fetchrow(
            '''
            SELECT *
            FROM public.users
            WHERE id = $1
            ''',
            user_id
        )

        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        birthday = StrUtils.to_str(request.json.get('birthday'))
        username = StrUtils.to_str(request.json.get('username'))
        role_id = IntUtils.to_int(request.json.get('role_id'))
        password = StrUtils.to_str(request.json.get('password'))
        reply_password = StrUtils.to_str(request.json.get('reply_password'))
        photo = StrUtils.to_str(request.json.get('photo'))
        status = IntUtils.to_int(request.json.get('status')) or 0

        if not first_name or not last_name:
            return response.json({
                '_success': False,
                'message': 'Required param(s): first_name or last_name'
            })

        if username:
            duplicate = await db.fetchrow(
                '''
                SELECT *
                FROM public.users
                WHERE id <> $1 AND username = $2
                ''',
                user_id,
                username
            )
            if duplicate:
                return response.json({
                    '_success': False,
                    'message': 'Duplicate: username'
                })

        else:
            return response.json({
                '_success': False,
                'message': 'Required param(s): username'
            })

        if password:
            if password == reply_password:
                password = password_to_hash(password)
            else:
                return response.json({
                    '_success': False,
                    'message': 'Password does not match'
                })

        else:
            password = customer['password']

        if not role_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): role_id'
            })

        user = await db.fetchrow(
            '''
            UPDATE public.users
            SET 
                last_name = $2,
                first_name = $3, 
                middle_name = $4, 
                role_id = $5, 
                password = $6, 
                username = $7, 
                photo = $8, 
                birthday = $9,
                status = $10
            WHERE id = $1
            RETURNING *
            ''',
            user_id,
            last_name,
            first_name,
            middle_name,
            role_id,
            password,
            username,
            photo,
            datetime.strptime(birthday, '%Y-%m-%d') if birthday else None,
            status
        )

        if not user:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True
        })

    async def delete(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return response.json({
                '_success': False,
                'message': 'Required param(s): user_id'
            })

        user = await db.fetchrow(
            '''
            UPDATE public.users
            SET status = -2
            WHERE id = $1
            RETURNING *
            ''',
            user_id
        )

        if not user:
            return response.json({
                '_success': False,
                'message': 'Operation failed'
            })

        return response.json({
            '_success': True
        })
