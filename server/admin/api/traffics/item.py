from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class TrafficsItemView(BaseAPIView):

    async def get(self, request, user, traffic_id):
        traffic_id = IntUtils.to_int(traffic_id)
        if not traffic_id:
            return self.error(message='Отсуствует обязательный параметры "traffic_id: int"')

        traffic = await db.fetchrow(
            '''
            SELECT t.*,
                ( 
                    CASE WHEN tk.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', tk.id,
                        'title', tk.title,
                    )
                    END
                ) AS track
            FROM public.traffics t
            LEFT JOIN public.tracks tk ON t.track_id = tk.id
            WHERE t.id = $1
            ''',
            traffic_id
        ) or {}

        return self.success(request=request, user=user, data={
            'traffic': dict(traffic)
        })

    async def post(self, request, user, traffic_id):
        traffic = await db.fetchrow(
            '''
            INSERT INTO public.traffics(title, description, track_id)
            VALUES ($1, $2, $3)
            RETURNING *
            ''',
            StrUtils.to_str(request.json.get('title')),
            StrUtils.to_str(request.json.get('description')),
            IntUtils.to_int(request.json.get('track_id')),
        )

        if not traffic:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'traffic': dict(traffic)
        })

    async def put(self, request, user, traffic_id):
        traffic_id = IntUtils.to_int(traffic_id)
        if not traffic_id:
            return self.error(message='Отсуствует обязательный параметр "traffic_id: int"')

        traffic = await db.fetchrow(
            '''
            UPDATE public.traffics
            SET title = $2, description = $3, track_id = $4
            WHERE id = $1
            RETURNING *
            ''',
            traffic_id,
            StrUtils.to_str(request.json.get('title')),
            StrUtils.to_str(request.json.get('description')),
            IntUtils.to_int(request.json.get('track_id'))
        )

        if not traffic:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'track': dict(traffic)
        })

    async def delete(self, request, user, traffic_id):
        traffic_id = IntUtils.to_int(traffic_id)
        if not traffic_id:
            return self.error(message='Отсуствует обязательный параметр "traffic_id: int"')

        traffic = await db.fetchrow(
            '''
            UPDATE public.traffics
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            traffic_id
        )

        if not traffic:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'traffic': dict(traffic)
        })
