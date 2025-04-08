import traceback
from datetime import datetime
from io import BytesIO

import xlsxwriter
from bson import ObjectId
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.states import ControlStatesRepository
from data.repository.types import ControlTypesRepository
from utils.strs import StrUtils


class ReceiptsReportsView(BaseAPIView):

    async def get(self, request, user):
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

        items = await mongo.receipts.find(filters) \
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
                'arrived_at': item['arrived_at'] and item['arrived_at'].date(),
                'billed_at': item['billed_at'] and item['billed_at'].date(),
                'before_weight': item['before_weight'],
                'after_weight': item['after_weight'],
                'description': item['description'],
                'state_id': item.get('state_id'),
                'type_id': item.get('type_id'),
                'stayed_day': item.get('stayed_day'),
                'company_id': item.get('company_id'),
            })

        types = await ControlTypesRepository.get_states() or {}
        states = await ControlStatesRepository.get_states() or {}

        companies = None
        if company_ids:
            companies = await mongo.companies.find({'_id': {'$in': company_ids}}).to_list(length=None)
            if companies:
                companies = {str(k['_id']): k for k in companies}

        titles = [
            dict(name='Дата принятия', width=19),
            dict(name='№ Вагонов', width=19),
            dict(name='Вид вагона', width=19),
            dict(name='Состаяние вагона', width=19),
            dict(name='Компания', width=19),
            dict(name='Дата выставление', width=19),
            dict(name='Вагона в сутки', width=19),
            dict(name='Изначальный весь', width=19),
            dict(name='Конечный весь', width=19),
        ]

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        headers = []
        widths = []
        for title in titles:
            headers.append(title['name'])
            widths.append(title['width'])

        bold_format = workbook.add_format({'bold': True, 'align': 'center'})
        worksheet.write_row(0, 0, headers, bold_format)
        for i in range(len(widths)):
            worksheet.set_column(i, i, widths[i])

        count = 1
        for receipt in receipts:
            worksheet.write_row(count, 0, [
                str(receipt['arrived_at'] or ''),
                receipt['track_id'],
                receipt['type_id'] in types and types[receipt['type_id']]['title'],
                receipt['state_id'] in states and states[receipt['state_id']]['title'],
                receipt['company_id'] in (companies or {}) and companies[receipt['company_id']]['title'],
                str(receipt['billed_at'] or ''),
                receipt['stayed_day'],
                receipt['before_weight'],
                receipt['after_weight'],
            ])
            count += 1

        workbook.close()
        contents.seek(0)

        return response.raw(
            contents.read(),
            headers={
                'Content-Disposition': 'attachment; filename=report.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
