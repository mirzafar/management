from core.db import db
from core.handlers import BaseAPIView
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreCategoriesView(BaseAPIView):
    template_name = 'admin/store-categories.html'

    async def get(self, request, user):
        parent_id = IntUtils.to_int(request.args.get('parent_id'))
        cond, cond_vars = ['is_active'], []

        parent = {}
        if parent_id:
            cond.append('parent_id = {}')
            cond_vars.append(parent_id)

            parent = await db.fetchrow(
                '''
                SELECT id, title, unit, description
                FROM public.categories
                WHERE id = $1
                ''',
                parent_id
            ) or {}

        cond, _ = set_counters(' AND '.join(cond))
        categories = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title, unit, description
            FROM public.categories
            WHERE %s
            ORDER BY id
            ''' % cond,
            *cond_vars
        ))

        return self.success(request=request, user=user, data={
            'categories': categories,
            'parent': dict(parent)
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        unit = StrUtils.to_str(request.json.get('unit'))
        if not unit:
            return self.error(message='Отсуствует обязательный параметры "Eдиница измерений"')

        description = StrUtils.to_str(request.json.get('description'))
        parent_id = IntUtils.to_int(request.json.get('parent_id'))

        item = await db.fetchrow(
            '''
            INSERT INTO public.categories(title, unit, description, parent_id)
            VALUES ($1, $2, $3, $4)
            RETURNING *          
            ''',
            title,
            unit,
            description,
            parent_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()


class StoreCategoryView(BaseAPIView):
    async def get(self, request, user, category_id):
        category_id = IntUtils.to_int(category_id)
        if not category_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        category = await db.fetchrow(
            '''
            SELECT title, unit, description
            FROM public.categories
            WHERE id = $1
            ''',
            category_id
        ) or {}

        return self.success(data={
            'category': dict(category)
        })

    async def put(self, request, user, category_id):
        category_id = IntUtils.to_int(category_id)
        if not category_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        unit = StrUtils.to_str(request.json.get('unit'))
        if not unit:
            return self.error(message='Отсуствует обязательный параметры "Eдиница измерений"')

        description = StrUtils.to_str(request.json.get('description'))

        item = await db.fetchrow(
            '''
            UPDATE public.categories
            SET title = $2, unit = $3, description = $4
            WHERE id = $1
            RETURNING *        
            ''',
            category_id,
            title,
            unit,
            description
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, category_id):
        category_id = IntUtils.to_int(category_id)
        if not category_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        item = await db.fetchrow(
            '''
            UPDATE public.categories
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *        
            ''',
            category_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
