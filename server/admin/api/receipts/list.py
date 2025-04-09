import traceback
from datetime import datetime, timedelta

from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from data.repository.states import ControlStatesRepository
from data.repository.types import ControlTypesRepository
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.strs import StrUtils


class ReceiptsView(BaseAPIView):
    template_name = 'admin/receipts.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 50))
        offset = IntUtils.to_int(request.args.get('offset')) or pager.offset

        start_arrived_at = StrUtils.to_str(request.args.get('start_arrived_at'))
        stop_arrived_at = StrUtils.to_str(request.args.get('stop_arrived_at'))
        track_id = StrUtils.to_str(request.args.get('track_id'))
        start_billed_at = StrUtils.to_str(request.args.get('start_billed_at'))
        stop_billed_at = StrUtils.to_str(request.args.get('stop_billed_at'))

        filters = {
            'is_active': True
        }

        if track_id:
            filters['track_id'] = {'$regex': track_id, '$options': 'i'}

        if start_arrived_at or stop_arrived_at:
            try:
                filters['arrived_at'] = {}

                if start_arrived_at:
                    start_arrived_at = datetime.strptime(start_arrived_at, '%Y-%m-%d')
                    filters['arrived_at']['$gte'] = start_arrived_at
                if stop_arrived_at:
                    stop_arrived_at = datetime.strptime(stop_arrived_at, '%Y-%m-%d')
                    filters['arrived_at']['$lte'] = stop_arrived_at

            except (Exception,):
                traceback.print_exc()

        if start_billed_at or stop_billed_at:
            try:
                filters['billed_at'] = {}

                if start_billed_at:
                    start_billed_at = datetime.strptime(start_billed_at, '%Y-%m-%d')
                    filters['billed_at']['$gte'] = start_billed_at
                if stop_billed_at:
                    stop_billed_at = datetime.strptime(stop_billed_at, '%Y-%m-%d')
                    filters['billed_at']['$lte'] = stop_billed_at

            except (Exception,):
                traceback.print_exc()

        items = await mongo.receipts.find(filters).skip(offset) \
            .limit(pager.limit) \
            .sort('_id', -1) \
            .to_list(length=None)

        receipts = []
        type_ids = []
        state_ids = []
        company_ids = []
        for item in items:
            if item.get('type_id'):
                type_ids.append(ObjectId(item['type_id']))
            if item.get('state_id'):
                state_ids.append(ObjectId(item['state_id']))

            if item.get('company_id'):
                company_ids.append(ObjectId(item['company_id']))

            receipts.append({
                '_id': str(item['_id']),
                'track_id': item['track_id'],
                'arrived_at': item['arrived_at'].date(),
                'billed_at': item['billed_at'] and item['billed_at'].date(),
                'before_weight': item['before_weight'],
                'after_weight': item['after_weight'],
                'description': item['description'],
                'state_id': item.get('state_id'),
                'type_id': item.get('type_id'),
                'stayed_day': item.get('stayed_day'),
                'company_id': item.get('company_id'),
            })

        types = await ControlTypesRepository.get_states()
        states = await ControlStatesRepository.get_states()

        companies = None
        if company_ids:
            companies = await mongo.companies.find({'_id': {'$in': company_ids}}).to_list(length=None)
            if companies:
                companies = {str(k['_id']): k for k in companies}

        pager.set_total(await mongo.receipts.count_documents(filters) or 0)

        return self.success(request=request, user=user, data={
            'receipts': receipts,
            'types': types,
            'states': states,
            'companies': companies,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        track_id = StrUtils.to_str(request.json.get('track_id'))
        arrived_at = StrUtils.to_str(request.json.get('arrived_at'))
        billed_at = StrUtils.to_str(request.json.get('billed_at'))
        before_weight = FloatUtils.to_float(request.json.get('before_weight'))
        after_weight = FloatUtils.to_float(request.json.get('after_weight'))
        description = StrUtils.to_str(request.json.get('description'))
        state_id = StrUtils.to_str(request.json.get('state_id'))
        type_id = StrUtils.to_str(request.json.get('type_id'))
        company_id = StrUtils.to_str(request.json.get('company_id'))

        if not track_id:
            return self.error(message='Отсуствует обязательный параметры "Номер вагона"')

        if arrived_at:
            try:
                arrived_at = datetime.strptime(arrived_at, '%Y-%m-%d')
            except (Exception,):
                traceback.print_exc()

        if not arrived_at:
            arrived_at = datetime.now()

        if billed_at:
            try:
                billed_at = datetime.strptime(billed_at, '%Y-%m-%d')
            except (Exception,):
                traceback.print_exc()

        stayed_day = None
        if arrived_at and billed_at:
            if arrived_at > billed_at:
                return self.error(message='Дата выставление не может быть больше чем дата принятия')
            stayed_day = (billed_at - arrived_at).days

        is_weighed = False
        if before_weight and after_weight:
            is_weighed = True

        if after_weight and before_weight and after_weight > before_weight:
            return self.error(message='Дата выставление не может быть больше чем дата принятия')

        data = {
            'track_id': track_id,
            'arrived_at': arrived_at,
            'billed_at': billed_at,
            'stayed_day': stayed_day,
            'before_weight': before_weight,
            'after_weight': after_weight,
            'is_weighed': is_weighed,
            'description': description,
            'state_id': state_id,
            'type_id': type_id,
            'company_id': company_id,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.receipts.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
            operations = []
            if arrived_at:
                operations.append({
                    'receipt_id': str(inserted.inserted_id),
                    'company_id': company_id,
                    'event': 'arrive',
                    'dtn': arrived_at
                })

            if billed_at:
                operations.append({
                    'receipt_id': str(inserted.inserted_id),
                    'company_id': company_id,
                    'event': 'bill',
                    'dtn': billed_at
                })

            if arrived_at and billed_at:
                current_date = arrived_at

                while current_date <= billed_at:
                    operations.append({
                        'receipt_id': str(inserted.inserted_id),
                        'company_id': company_id,
                        'event': 'stay',
                        'dtn': current_date
                    })
                    current_date += timedelta(days=1)

            if operations:
                await mongo.db.lagging_receipts.insert_many(operations)

        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'receipt': data
        })
