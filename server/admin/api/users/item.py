import asyncpg

from core.cache import cache
from core.datetimes import DatetimeUtils
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
            return self.error(message='Required param(s): user_id')

        employee = await db.fetchrow(
            '''
            SELECT *
            FROM public.users
            WHERE id = $1
            ''',
            user_id
        )

        if not employee:
            return self.error(message='Пользователь не найден(-o, -а) в системе')

        roles = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.roles
            WHERE status = 0
            '''
        ))

        return self.success(request=request, user=user, data={
            'employee': dict(employee),
            'roles': roles
        })

    async def post(self, request, user, user_id):
        first_name = StrUtils.to_str(request.json.get('first_name'))
        last_name = StrUtils.to_str(request.json.get('last_name'))
        middle_name = StrUtils.to_str(request.json.get('middle_name'))
        birthday = DatetimeUtils.parse(request.json.get('birthday'))
        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))
        role_id = IntUtils.to_int(request.json.get('role_id'))
        photo = StrUtils.to_str(request.json.get('photo'))

        if not first_name:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        if not username:
            return self.error(message='Отсуствует обязательный параметр "Логин"')

        if not password:
            return self.error(message='Отсуствует обязательный параметр "Пароль"')

        try:
            user = await db.fetchrow(
                '''
                INSERT INTO public.users
                (last_name, first_name, middle_name, password, username, photo, birthday, role_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
                ''',
                last_name,
                first_name,
                middle_name,
                password_to_hash(password),
                username,
                photo,
                birthday,
                role_id
            )
        except asyncpg.exceptions.UniqueViolationError:
            return self.error(
                message='Пользователь с этими значениями уже существует. Дубликат не может быть создан'
            )


        if not user:
            return self.error(message='Операция не выполнена')

        return self.success(data={'user': dict(user)})

    async def put(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return self.error(message='Отсуствует обязательный параметр "user_id: int"')

        action = StrUtils.to_str(request.json.get('action'))
        if action == 'main':
            first_name = StrUtils.to_str(request.json.get('first_name'))
            last_name = StrUtils.to_str(request.json.get('last_name'))
            middle_name = StrUtils.to_str(request.json.get('middle_name'))
            role_id = IntUtils.to_int(request.json.get('role_id'))
            birthday = DatetimeUtils.parse(request.json.get('birthday'))
            username = StrUtils.to_str(request.json.get('username'))
            photo = StrUtils.to_str(request.json.get('photo'))
            password = StrUtils.to_str(request.json.get('password'))

            if not first_name:
                return self.error(message='Отсуствует обязательный параметры "Имя"')

            if not username:
                return self.error(message='Отсуствует обязательный параметр "Логин"')

            try:
                user = await db.fetchrow(
                    '''
                    UPDATE public.users
                    SET 
                        last_name = $2,
                        first_name = $3, 
                        middle_name = $4, 
                        username = $5, 
                        photo = $6, 
                        birthday = $7,
                        role_id = $8
                    WHERE id = $1
                    RETURNING *
                    ''',
                    user_id,
                    last_name,
                    first_name,
                    middle_name,
                    username,
                    photo,
                    birthday,
                    role_id
                )
            except asyncpg.exceptions.UniqueViolationError:
                return self.error(
                    message='Пользователь с этими значениями уже существует. Дубликат не может быть создан'
                )

            if not user:
                return self.error(message='Операция не выполнена')

            if password:
                await db.fetchrow(
                    '''
                    UPDATE public.users
                    SET password = $2
                    WHERE id = $1
                    RETURNING *
                    ''',
                    user_id,
                    password_to_hash(password)
                )

            await cache.delete(f'users:{user["id"]}')

            return self.success(data={'user': dict(user)})

        elif action == 'reset_password':
            password = StrUtils.to_str(request.json.get('password'))
            if not password:
                return self.error(message='Отсуствует обязательный параметр "Пароль"')

            user = await db.fetchrow(
                '''
                UPDATE public.users
                SET password = $2
                WHERE id = $1
                RETURNING *
                ''',
                user_id,
                password_to_hash(password)
            )
            if not user:
                return self.error(message='Операция не выполнена')

            return self.success(data={
                'user': dict(user)
            })

        return self.error()

    async def delete(self, request, user, user_id):
        user_id = IntUtils.to_int(user_id)
        if not user_id:
            return self.error(message='Отсуствует обязательный параметр "user_id: int"')

        user = await db.fetchrow(
            '''
            DELETE FROM public.users
            WHERE id = $1
            RETURNING *
            ''',
            user_id
        )

        if not user:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'user': dict(user)
        })
