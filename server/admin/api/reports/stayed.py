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
    template_name = 'admin/reports-stayed.html'

    async def get(self, request, user):
        action = request.args.get('action')
        if action == 'generate':
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

            titles = [
                dict(name='№ п/п', width=19),
                dict(name='Наименование', width=38),
            ]
            t = [
                '',
                'Услуги по отстою вагонов',
            ]

            current_date = started_at

            date_keys = []
            while current_date <= stopped_at:
                titles.append(dict(name=datetime.strftime(current_date, '%Y-%m-%d'), width=19, join_column=3))
                t.extend(['принято', 'отстой', 'ушли'])
                date_keys.append(str(current_date.date()))
                current_date += timedelta(days=1)

            titles.append(dict(name='Общие итоги', width=19, join_column=3))
            t.extend(['принято', 'отстой', 'ушли'])

            widths = []
            bold_format = workbook.add_format({'bold': True, 'align': 'center'})
            i = 0
            for title in titles:
                if title.get('join_column'):
                    worksheet.merge_range(0, i, 0, i + title['join_column'] - 1, title['name'], bold_format)
                    i += title['join_column']
                else:
                    worksheet.write(0, i, title['name'], bold_format)
                    i += 1
                widths.append(title['width'])

            for i in range(len(widths)):
                worksheet.set_column(i, i, widths[i])
            worksheet.write_row(1, 0, t)

            company_ids = []
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

                if 'arrive' not in data[x['company_id']][x['date']]:
                    data[x['company_id']][x['date']]['arrive'] = 0

                data[x['company_id']][x['date']]['arrive'] += (x.get('count') or 0)

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

                if 'bill' not in data[b['company_id']][b['date']]:
                    data[b['company_id']][b['date']]['bill'] = 0

                data[b['company_id']][b['date']]['bill'] += (b.get('count') or 0)

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

                if 'stay' not in data[s['company_id']][s['date']]:
                    data[s['company_id']][s['date']]['stay'] = 0

                data[s['company_id']][s['date']]['stay'] += (s.get('count') or 0)

            companies = await mongo.companies.find({'_id': {'$in': company_ids}}).to_list(length=None)
            companies = {str(v['_id']): v['title'] for v in companies}

            count = 2
            index = 1
            for k, v in data.items():
                l = [
                    index,
                    companies[k]
                ]

                company_arrive_count = 0
                company_bill_count = 0
                company_stay_count = 0

                for d in date_keys:
                    if d in v:
                        company_arrive_count += v[d].get('arrive') or 0
                        company_bill_count += v[d].get('bill') or 0
                        company_stay_count += v[d].get('stay') or 0
                        l.extend([
                            v[d].get('arrive') or 0,
                            v[d].get('stay') or 0,
                            v[d].get('bill') or 0,
                        ])
                    else:
                        l.extend([0, 0, 0])

                l.extend([
                    company_arrive_count,
                    company_stay_count,
                    company_bill_count
                ])

                worksheet.write_row(count, 0, l)
                index += 1
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

        return self.success(request=request, user=user, data={})
