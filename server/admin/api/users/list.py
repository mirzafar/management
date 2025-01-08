import asyncpg

from core.datetimes import DatetimeUtils
from core.db import db
from core.handlers import BaseAPIView
from core.hasher import password_to_hash
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class EmployeesView(BaseAPIView):

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 50))

        query = StrUtils.to_str(request.args.get('query'))

        cond, cond_vars = ['u.is_active'], []

        if query:
            cond.append('(u.first_name ILIKE {same} OR u.last_name ILIKE {})')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))
        users = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT u.*
            FROM public.users u
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.users u
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0

        return self.success(request=request, user=user, data={
            'users': users,
            'total': total,
        })

    async def post(self, request, user):
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

        if not last_name:
            return self.error(message='Отсуствует обязательный параметры "Фамилия"')

        if not username:
            return self.error(message='Отсуствует обязательный параметр "Логин"')

        if not password:
            return self.error(message='Отсуствует обязательный параметр "Пароль"')

        try:
            item = await db.fetchrow(
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
            ) or {}

        except asyncpg.exceptions.UniqueViolationError:
            return self.error(
                message='Пользователь с этими значениями уже существует. Дубликат не может быть создан'
            )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success(data={'user': dict(item)})
