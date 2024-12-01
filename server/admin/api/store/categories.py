from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreCategoriesView(BaseAPIView):
    template_name = 'admin/store-categories.html'

    async def get(self, request, user):
        categories = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title, unit, description
            FROM public.categories
            WHERE is_active
            ORDER BY id DESC
            '''
        ))

        return self.success(request=request, user=user, data={
            'categories': categories
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        unit = StrUtils.to_str(request.json.get('unit'))
        if not unit:
            return self.error(message='Отсуствует обязательный параметры "Eдиница измерений"')

        description = StrUtils.to_str(request.json.get('description'))
        if not unit:
            return self.error(message='Отсуствует обязательный параметры "Eдиница измерений"')

        item = await db.fetchrow(
            '''
            INSERT INTO public.categories(title, unit, description)
            VALUES ($1, $2, $3)
            RETURNING *          
            ''',
            title,
            unit,
            description
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
        if not unit:
            return self.error(message='Отсуствует обязательный параметры "Eдиница измерений"')

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
