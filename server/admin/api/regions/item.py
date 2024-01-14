from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class RegionsItemView(BaseAPIView):

    async def get(self, request, user, region_id):
        region_id = IntUtils.to_int(region_id)
        if not region_id:
            return self.error(message='Отсуствует обязательный параметры "region_id: int"')

        region = await db.fetchrow(
            '''
            SELECT r.*,
                (
                    CASE WHEN d.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', d.id,
                        'title', d.title,
                        'number', d.number
                    )
                    END
                ) AS district
            FROM public.regions r
            LEFT JOIN public.districts d ON d.id = r.district_id
            WHERE r.id = $1
            ''',
            region_id
        ) or {}

        return self.success(request=request, user=user, data={
            'region': dict(region)
        })

    async def post(self, request, user, region_id):
        region = await db.fetchrow(
            '''
            INSERT INTO public.regions(title, district_id)
            VALUES ($1)
            RETURNING *
            ''',
            StrUtils.to_str(request.json.get('title')),
            IntUtils.to_int(request.json.get('district_id')),
        )

        if not region:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'region': dict(region)
        })

    async def put(self, request, user, region_id):
        region_id = IntUtils.to_int(region_id)
        if not region_id:
            return self.error(message='Отсуствует обязательный параметр "region_id: int"')

        region = await db.fetchrow(
            '''
            UPDATE public.regions
            SET title = $2, district_id = $3
            WHERE id = $1
            RETURNING *
            ''',
            region_id,
            StrUtils.to_str(request.json.get('title')),
            IntUtils.to_int(request.json.get('district_id'))
        )

        if not region:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'region': dict(region)
        })

    async def delete(self, request, user, region_id):
        region_id = IntUtils.to_int(region_id)
        if not region_id:
            return self.error(message='Отсуствует обязательный параметр "region_id: int"')

        region = await db.fetchrow(
            '''
            UPDATE public.regions
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            region_id
        )

        if not region:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'region': dict(region)
        })
