from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class DistrictsItemView(BaseAPIView):

    async def get(self, request, user, district_id):
        district_id = IntUtils.to_int(district_id)
        if not district_id:
            return self.error(message='Отсуствует обязательный параметры "district_id: int"')

        district = await db.fetchrow(
            '''
            SELECT *
            FROM public.districts
            WHERE id = $1
            ''',
            district_id
        ) or {}

        return self.success(request=request, user=user, data={
            'district': dict(district)
        })

    async def post(self, request, user, district_id):
        district = await db.fetchrow(
            '''
            INSERT INTO public.districts(title, number)
            VALUES ($1, $2)
            RETURNING *
            ''',
            StrUtils.to_str(request.json.get('title')),
            IntUtils.to_int(request.json.get('number'))
        )

        if not district:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'district': dict(district)
        })

    async def put(self, request, user, district_id):
        district_id = IntUtils.to_int(district_id)
        if not district_id:
            return self.error(message='Отсуствует обязательный параметр "district_id: int"')

        district = await db.fetchrow(
            '''
            UPDATE public.districts
            SET title = $2, number = $3
            WHERE id = $1
            RETURNING *
            ''',
            district_id,
            StrUtils.to_str(request.json.get('title')),
            IntUtils.to_int(request.json.get('number'))
        )

        if not district:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'district': dict(district)
        })

    async def delete(self, request, user, district_id):
        district_id = IntUtils.to_int(district_id)
        if not district_id:
            return self.error(message='Отсуствует обязательный параметр "district_id: int"')

        district = await db.fetchrow(
            '''
            UPDATE public.districts
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            district_id
        )

        if not district:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'district': dict(district)
        })
