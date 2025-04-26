import traceback
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter
from bson import ObjectId
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from utils.strs import StrUtils


class StayedReportsView(BaseAPIView):

    async def get(self, request, user):
        started_at = StrUtils.to_str(request.args.get('started_at'))
        stopped_at = StrUtils.to_str(request.args.get('stopped_at'))

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

        started_at = started_at - timedelta(days=1)

        data = {}

        arrive_data = await mongo.lagging_receipts.aggregate([
            {
                '$match': {
                    'dtn': {
                        '$gte': started_at,
                        '$lte': stopped_at
                    },
                    'event': 'arrive'
                }
            },
            {
                '$group': {
                    '_id': {
                        'company_id': '$company_id',
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
                    'company_id': '$_id.company_id',
                    'date': '$_id.date',
                    'count': 1
                }
            }
        ]).to_list(length=None)

        bill_data = await mongo.lagging_receipts.aggregate([
            {
                '$match': {
                    'dtn': {
                        '$gte': started_at,
                        '$lte': stopped_at
                    },
                    'event': 'bill'
                }
            },
            {
                '$group': {
                    '_id': {
                        'company_id': '$company_id',
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
                    'company_id': '$_id.company_id',
                    'date': '$_id.date',
                    'count': 1
                }
            }
        ]).to_list(length=None)

        stay_data = await mongo.lagging_receipts.aggregate([
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
                        'company_id': '$company_id',
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
                    'company_id': '$_id.company_id',
                    'date': '$_id.date',
                    'count': 1
                }
            }
        ]).to_list(length=None)

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        headers = [
            dict(name='№ п/п', width=5),
            dict(name='Наименование', width=38),
        ]
        titles = [
            '',
            'Услуги по отстою вагонов',
        ]

        current_date = started_at

        date_keys = []
        while current_date <= stopped_at:
            headers.append(dict(name=datetime.strftime(current_date, '%d.%m.%Y'), join_column=3, width=5))
            titles.extend(['прин', 'отс', 'ушл'])
            date_keys.append(str(current_date.date()))
            current_date += timedelta(days=1)

        headers.append(dict(name='Общие итоги', width=3, join_column=3))
        titles.extend(['прин', 'отс', 'ушл'])

        widths = []
        i = 0
        for header in headers:
            if header.get('join_column'):
                worksheet.merge_range(0, i, 0, i + header['join_column'] - 1, header['name'],
                                      workbook.add_format({'bold': True, 'align': 'center', 'border': 1}))
                i += header['join_column']
                widths.extend([header['width']] * 3)
            else:
                worksheet.write(0, i, header['name'],
                                workbook.add_format({'bold': True, 'align': 'center', 'border': 1}))
                i += 1
                widths.append(header['width'])

        for i in range(len(widths)):
            worksheet.set_column(i, i, widths[i])

        i = 0
        for title in titles:
            if title == 'отс':
                worksheet.write(1, i, title,
                                workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'blue'}))
            elif title == 'ушл':
                worksheet.write(1, i, title, workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'red'}))
            else:
                worksheet.write(1, i, title, workbook.add_format({'align': 'center', 'border': 1}))
            i += 1

        company_ids = []
        total_by_dates = {'all': {'arrive': 0, 'bill': 0, 'stay': 0}}

        for x in arrive_data:
            if not x.get('company_id'):
                continue

            company_ids.append(ObjectId(x['company_id']))
            if x['company_id'] not in data:
                data[x['company_id']] = {}
                for d in date_keys:
                    data[x['company_id']][d] = {}

            if x['date'] not in data[x['company_id']]:
                data[x['company_id']][x['date']] = {}

            if x['date'] not in total_by_dates:
                total_by_dates[x['date']] = {}

            if 'arrive' not in data[x['company_id']][x['date']]:
                data[x['company_id']][x['date']]['arrive'] = 0

            if 'arrive' not in total_by_dates[x['date']]:
                total_by_dates[x['date']]['arrive'] = 0

            data[x['company_id']][x['date']]['arrive'] += (x.get('count') or 0)
            total_by_dates[x['date']]['arrive'] += (x.get('count') or 0)

        for b in bill_data:
            if not b.get('company_id'):
                continue

            company_ids.append(ObjectId(b['company_id']))
            if b['company_id'] not in data:
                data[b['company_id']] = {}
                for d in date_keys:
                    data[b['company_id']][d] = {}

            if b['date'] not in data[b['company_id']]:
                data[b['company_id']][b['date']] = {}

            if b['date'] not in total_by_dates:
                total_by_dates[b['date']] = {}

            if 'bill' not in data[b['company_id']][b['date']]:
                data[b['company_id']][b['date']]['bill'] = 0

            if 'bill' not in total_by_dates[b['date']]:
                total_by_dates[b['date']]['bill'] = 0

            data[b['company_id']][b['date']]['bill'] += (b.get('count') or 0)
            total_by_dates[b['date']]['bill'] += (b.get('count') or 0)

        for s in stay_data:
            if not s.get('company_id'):
                continue

            company_ids.append(ObjectId(s['company_id']))
            if s['company_id'] not in data:
                data[s['company_id']] = {}
                for d in date_keys:
                    data[s['company_id']][d] = {}

            if s['date'] not in data[s['company_id']]:
                data[s['company_id']][s['date']] = {}

            if s['date'] not in total_by_dates:
                total_by_dates[s['date']] = {}

            if 'stay' not in data[s['company_id']][s['date']]:
                data[s['company_id']][s['date']]['stay'] = 0

            if 'stay' not in total_by_dates[s['date']]:
                total_by_dates[s['date']]['stay'] = 0

            data[s['company_id']][s['date']]['stay'] += (s.get('count') or 0)
            total_by_dates[s['date']]['stay'] += (s.get('count') or 0)

        companies = await mongo.companies.find({'_id': {'$in': company_ids}}).to_list(length=None)
        companies = {str(v['_id']): v['title'] for v in companies}

        count = 2
        index = 1
        for k, v in data.items():
            i = 0

            worksheet.write(count, i, index, workbook.add_format({'align': 'center', 'border': 1}))
            i += 1

            worksheet.write(count, i, companies[k], workbook.add_format({'align': 'center', 'border': 1}))
            i += 1

            company_arrive_count = 0
            company_bill_count = 0
            company_stay_count = 0

            for d in date_keys:
                if d in v:
                    company_arrive_count += v[d].get('arrive') or 0
                    company_bill_count += v[d].get('bill') or 0
                    company_stay_count += v[d].get('stay') or 0

                    worksheet.write(count, i, v[d].get('arrive') or 0,
                                    workbook.add_format({'align': 'center', 'border': 1}))
                    i += 1

                    worksheet.write(count, i, v[d].get('stay') or 0,
                                    workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'blue'}))
                    i += 1

                    worksheet.write(count, i, v[d].get('bill') or 0,
                                    workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'red'}))
                    i += 1

                else:
                    worksheet.write(count, i, 0,
                                    workbook.add_format({'align': 'center', 'border': 1}))
                    i += 1

                    worksheet.write(count, i, 0,
                                    workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'blue'}))
                    i += 1

                    worksheet.write(count, i, 0,
                                    workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'red'}))
                    i += 1

            worksheet.write(count, i, company_arrive_count,
                            workbook.add_format({'align': 'center', 'border': 1}))
            i += 1

            worksheet.write(count, i, company_stay_count,
                            workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'blue'}))
            i += 1

            worksheet.write(count, i, company_bill_count,
                            workbook.add_format({'align': 'center', 'border': 1, 'font_color': 'red'}))
            i += 1

            total_by_dates['all']['arrive'] += company_arrive_count
            total_by_dates['all']['bill'] += company_bill_count
            total_by_dates['all']['stay'] += company_stay_count

            index += 1
            count += 1

        i = 1
        worksheet.write(count, i, 'Итого:',
                        workbook.add_format({'align': 'center'}))
        i += 1

        for d in date_keys:
            if d in total_by_dates:
                worksheet.write(count, i, total_by_dates[d].get('arrive') or 0,
                                workbook.add_format({'align': 'center'}))
                i += 1

                worksheet.write(count, i, total_by_dates[d].get('stay') or 0,
                                workbook.add_format({'align': 'center', 'font_color': 'blue'}))
                i += 1

                worksheet.write(count, i, total_by_dates[d].get('bill') or 0,
                                workbook.add_format({'align': 'center', 'font_color': 'red'}))
                i += 1

            else:
                worksheet.write(count, i, 0,
                                workbook.add_format({'align': 'center'}))
                i += 1

                worksheet.write(count, i, 0,
                                workbook.add_format({'align': 'center', 'font_color': 'blue'}))
                i += 1

                worksheet.write(count, i, 0,
                                workbook.add_format({'align': 'center', 'font_color': 'red'}))
                i += 1

        worksheet.write(count, i, total_by_dates['all']['arrive'],
                        workbook.add_format({'align': 'center'}))
        i += 1

        worksheet.write(count, i, total_by_dates['all']['stay'],
                        workbook.add_format({'align': 'center', 'font_color': 'blue'}))
        i += 1

        worksheet.write(count, i, total_by_dates['all']['bill'],
                        workbook.add_format({'align': 'center', 'font_color': 'red'}))
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
