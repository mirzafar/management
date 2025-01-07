import asyncpg

from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from core.hasher import password_to_hash
from utils.ints import IntUtils
from utils.strs import StrUtils


class EmployeeView(BaseAPIView):

    async def get(self, request, user, employee_id):
        employee_id = IntUtils.to_int(employee_id)
        if not employee_id:
            return self.error(message='Required param(s): employee_id')

        item = await db.fetchrow(
            '''
            SELECT *
            FROM public.users
            WHERE id = $1
            ''',
            employee_id
        ) or {}

        if not item:
            return self.error(message='Пользователь не найден(-o, -а) в системе')

        return self.success(request=request, user=user, data={
            'employee': dict(item)
        })

    async def put(self, request, user, employee_id):
        employee_id = IntUtils.to_int(employee_id)
        if not employee_id:
            return self.error(message='Required param(s): employee_id')

        action = StrUtils.to_str(request.json.get('action'))
        if action == 'main':
            first_name = StrUtils.to_str(request.json.get('first_name'))
            last_name = StrUtils.to_str(request.json.get('last_name'))
            middle_name = StrUtils.to_str(request.json.get('middle_name'))
            role_id = IntUtils.to_int(request.json.get('role_id'))
            birthday = DatetimeUtils.parse(request.json.get('birthday'))
            username = StrUtils.to_str(request.json.get('username'))
            photo = StrUtils.to_str(request.json.get('photo'))

            if not first_name:
                return self.error(message='Отсуствует обязательный параметры "Имя"')

            if not last_name:
                return self.error(message='Отсуствует обязательный параметры "Фамилия"')

            if not username:
                return self.error(message='Отсуствует обязательный параметр "Логин"')

            try:
                item = await db.fetchrow(
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
                    employee_id,
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

            if not item:
                return self.error(message='Операция не выполнена')
            return self.success(data={'employee': dict(item)})

        elif action == 'reset_password':
            password = StrUtils.to_str(request.json.get('password'))
            if not password:
                return self.error(message='Отсуствует обязательный параметр "Пароль"')

            item = await db.fetchrow(
                '''
                UPDATE public.users
                SET password = $2
                WHERE id = $1
                RETURNING *
                ''',
                employee_id,
                password_to_hash(password)
            )
            if not item:
                return self.error(message='Операция не выполнена')

            return self.success(data={
                'employee': dict(item)
            })

        elif action == 'blocked':
            item = await db.fetchrow(
                '''
                UPDATE public.users
                SET is_blocked = TRUE
                WHERE id = $1
                RETURNING *
                ''',
                employee_id
            )
            if not item:
                return self.error(message='Операция не выполнена')

            return self.success(data={
                'employee': dict(item)
            })

        elif action == 'unblocked':
            item = await db.fetchrow(
                '''
                UPDATE public.users
                SET is_blocked = FALSE
                WHERE id = $1
                RETURNING *
                ''',
                employee_id
            )
            if not item:
                return self.error(message='Операция не выполнена')

            return self.success(data={
                'employee': dict(item)
            })

        return self.error()

    async def delete(self, request, user, employee_id):
        employee_id = IntUtils.to_int(employee_id)
        if not employee_id:
            return self.error(message='Отсуствует обязательный параметр "employee_id: int"')

        item = await db.fetchrow(
            '''
            UPDATE public.users
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *
            ''',
            employee_id
        ) or {}

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'employee_id': dict(item)
        })
