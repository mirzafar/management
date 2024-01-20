from datetime import datetime

import polars as pl
from polars.exceptions import ColumnNotFoundError
from pymongo import UpdateOne

from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from settings import settings
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils

TrackStatuses = {
    1: 'В процессе',
    2: 'В складе производства',
    3: 'Покинул(-а) старну производства',
    4: 'В складе Казахстан(Алматы)',
    5: 'Прибыл',
}


class ExportTracksView(BaseAPIView):
    template_name = 'admin/cargo/export-tracks.html'

    async def get(self, request, user):
        return self.success(request=request, user=user, data={
            'statuses': [{'key': k, 'value': v} for k, v in TrackStatuses.items()]
        })

    async def post(self, request, user):
        action = request.json.get('action', 'insert')
        if action == 'excel_to_data':
            file_path = request.json.get('file_path')
            number_column = IntUtils.to_int(request.json.get('number_column'), default=1)

            if not file_path:
                return self.error(message='Отсуствует обязательный параметр "file_path: str"')

            excel = pl.read_excel(
                source='/'.join(settings['root_dir'].split('/')[:-1]) + '/static/uploads/' + file_path,
                read_csv_options={"has_header": False}
            )
            try:
                tracks = ListUtils.to_list_of_strs(excel.get_column(f'column_{number_column}').to_list(), distinct=True)
            except (ColumnNotFoundError,):
                return self.error(message='Операция не выполнена')

            if tracks:
                data = await mongo.tracks.find({'track_id': {'$in': tracks}}).to_list(length=None) or []
                items = data + [
                    {
                        'track_id': x,
                    } for x in list(set(tracks) - set([i['track_id'] for i in data]))
                ]

                return self.success(data={
                    'items': items,
                    'statuses': TrackStatuses
                })

        elif action == 'insert':
            track_ids = ListUtils.to_list_of_strs(request.json.get('track_ids'))
            track_id = StrUtils.to_str(request.json.get('track_id'))
            status = IntUtils.to_int(request.json.get('status'), default=1)
            if not track_ids:
                if track_id:
                    track_ids = [track_id]
                else:
                    return self.error(message='Отсуствует обязательный параметр "track_ids: list"')

            aggregators = []
            for x in track_ids:
                aggregators.append(UpdateOne({'track_id': x}, {'$set': {
                    'status': status,
                    'updated_at': datetime.now()
                }}, upsert=True))

            await mongo.tracks.bulk_write(aggregators)

        return self.success()


class CustomerTracksView(BaseAPIView):
    template_name = 'admin/cargo/customer-tracks.html'

    async def get(self, request, user):
        return self.success(request=request, user=user, data={
            'statuses': [{'key': k, 'value': v} for k, v in TrackStatuses.items()]
        })

    async def post(self, request, user):
        track_id = StrUtils.to_str(request.json.get('track_id'))
        if not track_id:
            return self.error(message='Отсуствует обязательный параметр "track_id: str"')

        await mongo.tracks.update_one({'track_id': track_id}, {'$set': {
            'customer_id': user['id'],
            'status': 1,
        }}, upsert=True)

        return self.success()

    async def delete(self, request, user):
        track_id = StrUtils.to_str(request.json.get('track_id'))
        if not track_id:
            return self.error(message='Отсуствует обязательный параметр "track_id: str"')

        await mongo.tracks.update_one({'track_id': track_id}, {'$unset': {
            'customer_id': '',
        }}, upsert=True)

        return self.success()


class TracksView(BaseAPIView):
    template_name = 'admin/cargo/tracks.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        status = IntUtils.to_int(request.args.get('status'))
        customer_id = IntUtils.to_int(request.args.get('customer_id'))

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))

        filters = {
            'status': {
                '$nin': [-1]
            },
            'customer_id': user['id'],
        }

        if query:
            filters['track_id'] = {'$regex': query, '$options': 'i'}

        if status:
            filters['status'] = status

        if customer_id:
            filters['customer_id'] = customer_id

        items = await mongo.tracks.find(filters) \
            .limit(pager.limit) \
            .skip(pager.offset) \
            .sort({'_id': -1}) \
            .to_list(length=None)

        return self.success(request=request, data={
            'items': items,
            'statuses': TrackStatuses,
        })
