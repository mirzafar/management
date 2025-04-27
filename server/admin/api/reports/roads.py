import traceback
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.roads import ControlRoadsRepository
from utils.strs import StrUtils


class RoadsReportsView(BaseAPIView):

    async def get(self, request, user):
        started_at = StrUtils.to_str(request.args.get('rd-started-at'))
        stopped_at = StrUtils.to_str(request.args.get('rd-stopped-at'))

        if started_at:
            try:
                started_at = datetime.strptime(started_at, '%Y-%m-%d')
            except (Exception,):
                traceback.print_exc()

        if stopped_at:
            try:
                stopped_at = datetime.strptime(stopped_at, '%Y-%m-%d')
            except (Exception,):
                traceback.print_exc()

        if not started_at:
            started_at = datetime.now()

        if not stopped_at:
            stopped_at = datetime.now()

        roads = await ControlRoadsRepository.get_roads()

        items = await mongo.lagging_receipts.aggregate([
            {
                '$match': {
                    'dtn': {
                        '$gte': started_at,
                        '$lte': stopped_at
                    },
                    'event': 'stay'
                }
            },
            {
                '$group': {
                    '_id': {
                        'road_id': '$road_id',
                        'date': {
                            '$dateToString': {'format': '%Y-%m-%d', 'date': '$dtn'}
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'road_id': '$_id.road_id',
                    'date': '$_id.date',
                    'count': 1
                }
            }
        ]).to_list(length=None)

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        headers = [
            dict(name='Путь', width=25),
        ]

        current_date = started_at

        date_keys = []
        while current_date <= stopped_at:
            headers.append(dict(name=datetime.strftime(current_date, '%d.%m.%Y'), width=10))
            date_keys.append(str(current_date.date()))
            current_date += timedelta(days=1)

        headers.append(dict(name='Общие итоги', width=12))

        widths = []
        i = 0
        for header in headers:
            worksheet.write(0, i, header['name'], workbook.add_format({'bold': True, 'align': 'center', 'border': 1}))
            i += 1
            widths.append(header['width'])

        for i in range(len(widths)):
            worksheet.set_column(i, i, widths[i])

        total_by_dates = {'all': 0}

        data = {}
        for item in items:
            if not item.get('road_id'):
                continue

            if item['road_id'] not in data:
                data[item['road_id']] = {}
                for d in date_keys:
                    data[item['road_id']][d] = 0

            if item['date'] not in data[item['road_id']]:
                data[item['road_id']][item['date']] = 0

            if item['date'] not in total_by_dates:
                total_by_dates[item['date']] = 0

            data[item['road_id']][item['date']] += (item.get('count') or 0)
            total_by_dates[item['date']] += (item.get('count') or 0)

        count = 1
        index = 1
        for k, v in data.items():
            i = 0

            worksheet.write(count, i, roads[k].get('title'), workbook.add_format({'align': 'center', 'border': 1}))
            i += 1

            total_count = 0
            for d in date_keys:
                if d in v:
                    total_count += v[d] or 0

                    worksheet.write(count, i, v[d] or 0, workbook.add_format({'align': 'center', 'border': 1}))
                    i += 1

                else:
                    worksheet.write(count, i, 0, workbook.add_format({'align': 'center', 'border': 1}))
                    i += 1

            worksheet.write(count, i, total_count, workbook.add_format({'align': 'center', 'border': 1}))
            i += 1

            total_by_dates['all'] += total_count
            index += 1

            count += 1

        i = 0

        worksheet.write(count, i, 'Итого:', workbook.add_format({'align': 'center'}))
        i += 1

        for d in date_keys:
            if d in total_by_dates:
                worksheet.write(count, i, total_by_dates[d] or 0, workbook.add_format({'align': 'center'}))
                i += 1

            else:
                worksheet.write(count, i, 0, workbook.add_format({'align': 'center'}))
                i += 1

        worksheet.write(count, i, total_by_dates['all'], workbook.add_format({'align': 'center'}))
        i += 1

        workbook.close()
        contents.seek(0)

        return response.raw(
            contents.read(),
            headers={
                'Content-Disposition': 'attachment; filename=report.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
