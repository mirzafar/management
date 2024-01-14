from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class TracksItemView(BaseAPIView):

    async def get(self, request, user, track_id):
        track_id = IntUtils.to_int(track_id)
        if not track_id:
            return self.error(message='Отсуствует обязательный параметры "track_id: int"')

        track = await db.fetchrow(
            '''
            SELECT t.*,
                ( 
                    CASE WHEN r.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', r.id,
                        'title', r.title,
                    )
                    END
                ) AS region,
                (
                    CASE WHEN d.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', d.id,
                        'title', d.title,
                        'number', d.number
                    )
                    END
                ) AS district
            FROM public.tracks t
            LEFT JOIN public.regions r ON r.id = t.region_id
            LEFT JOIN public.districts d ON d.id = r.district_id
            WHERE t.id = $1
            ''',
            track_id
        ) or {}

        return self.success(request=request, user=user, data={
            'track': dict(track)
        })

    async def post(self, request, user, track_id):
        track = await db.fetchrow(
            '''
            INSERT INTO public.tracks(title, description, region_id)
            VALUES ($1)
            RETURNING *
            ''',
            StrUtils.to_str(request.json.get('title')),
            StrUtils.to_str(request.json.get('description')),
            IntUtils.to_int(request.json.get('district_id')),
        )

        if not track:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'track': dict(track)
        })

    async def put(self, request, user, track_id):
        track_id = IntUtils.to_int(track_id)
        if not track_id:
            return self.error(message='Отсуствует обязательный параметр "track_id: int"')

        track = await db.fetchrow(
            '''
            UPDATE public.tracks
            SET title = $2, description = $3, region_id = $4
            WHERE id = $1
            RETURNING *
            ''',
            track_id,
            StrUtils.to_str(request.json.get('title')),
            StrUtils.to_str(request.json.get('description')),
            IntUtils.to_int(request.json.get('region_id'))
        )

        if not track:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'track': dict(track)
        })

    async def delete(self, request, user, track_id):
        track_id = IntUtils.to_int(track_id)
        if not track_id:
            return self.error(message='Отсуствует обязательный параметр "track_id: int"')

        track = await db.fetchrow(
            '''
            UPDATE public.tracks
            SET status = -1
            WHERE id = $1
            RETURNING *
            ''',
            track_id
        )

        if not track:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'track': dict(track)
        })
