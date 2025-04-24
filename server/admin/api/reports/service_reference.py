import calendar
from datetime import datetime
from io import BytesIO

import xlsxwriter
from bson import ObjectId
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.companies import ControlCompaniesRepository
from utils.ints import IntUtils


class ServicesReferenceReportsView(BaseAPIView):
    MONTH_TITLE = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }

    async def get(self, request, user):
        now = datetime.now()
        month = IntUtils.to_int(request.args.get('r-month')) or now.month
        year = IntUtils.to_int(request.args.get('r-year')) or now.year

        first_day = datetime(year=year, month=month, day=1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        header_title = f'Справка о железнодорожных услугах за {self.MONTH_TITLE.get(month)} месяц {year} года.'
        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'border': 1
        })
        bold_format = workbook.add_format({'bold': True, 'align': 'center', 'text_wrap': True, 'valign': 'vcenter'})
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'font_size': 16
        })

        #  setting header
        worksheet.merge_range(0, 0, 0, 10 - 1, header_title, header_format)
        # worksheet.set_column(0, 0, 220)

        # setting title
        titles = [
            dict(name='№', width=3),
            dict(name='Контрагенты, компании', width=40),
            dict(name='Наименование услуг', width=20),
            dict(name='К-во вагон', width=8),
            dict(name='К-во ваг/сут', width=8),
            dict(name='Аренда весов', width=8),
            dict(name='Взвешивание', width=10),
            dict(name='Аренда м/кв', width=8),
            dict(name='Цена за услуги', width=18),
            dict(name='Сумма, тенге', width=18),
        ]

        widths, i = [], 0
        for title in titles:
            if title.get('join_column'):
                worksheet.merge_range(2, i, 0, i + title['join_column'] - 1, title['name'], title_format)
                i += title['join_column']
            else:
                worksheet.write(2, i, title['name'], title_format)
                i += 1
            widths.append(title['width'])

        for i in range(len(widths)):
            worksheet.set_column(i, i, widths[i])

        items = await mongo.lagging_receipts.aggregate([
            {
                '$match': {
                    'dtn': {
                        '$gte': first_day,
                        '$lte': last_day
                    },
                    'event': 'arrive'
                }
            },
            {
                '$group': {
                    '_id': '$company_id',
                    'total': {'$sum': 1},
                    'weighed_count': {'$sum': {'$toInt': '$is_weighed'}}
                }
            }
        ]).to_list(length=None)

        data = {}

        for item in items:
            if not ObjectId.is_valid(item.get('_id')):
                continue

            if item['_id'] not in data:
                data[item['_id']] = {
                    'arrive': item['total'] or 0,
                    'weighed_count': item['weighed_count'] or 0,
                }

        items = await mongo.lagging_receipts.aggregate([
            {
                '$match': {
                    'dtn': {
                        '$gte': first_day,
                        '$lte': last_day
                    },
                    'event': 'stay'
                }
            },
            {
                '$group': {
                    '_id': '$company_id',
                    'total': {'$sum': 1}
                }
            }
        ]).to_list(length=None)

        for item in items:
            if not ObjectId.is_valid(item.get('_id')):
                continue

            if item['_id'] not in data:
                data[item['_id']] = {
                    'stay': item['total'] or 0,
                }

            if 'stay' not in data[item['_id']]:
                data[item['_id']]['stay'] = item['total'] or 0

            data[item['_id']]['stay'] += item['total']

        companies = await ControlCompaniesRepository.get_companies()
        total_arrive = 0
        total_weighed = 0
        total_stay = 0
        for key, value in companies.items():
            if key not in data:
                data[key] = {}

            data[key]['title'] = value['title']
            data[key]['sum_cleaning'] = value['sum_cleaning'] or 0
            data[key]['sum_stay'] = value['sum_stay'] or 0
            data[key]['sum_weighing'] = value['sum_weighing'] or 0
            data[key]['sum_rent_scale'] = value['sum_rent_scale'] or 0
            data[key]['sum_rent_m'] = value['sum_rent_m'] or 0

            #  calc total
            total_arrive += (data[key].get('arrive') or 0)
            total_stay += (data[key].get('stay') or 0)
            total_weighed += (data[key].get('weighed_count') or 0)

        count = 3
        index = 1

        total_sum = 0
        border_format = workbook.add_format({'border': 1})
        for key, value in data.items():
            use_title = True
            if value.get('arrive'):
                worksheet.write_row(count, 0, [
                    use_title and index or '',
                    use_title and value['title'] or '',
                    'Под-уборка',
                    value['arrive'],
                    '', '', '', '',
                    value['sum_cleaning'] or 0,
                    (value['sum_cleaning'] or 0) * value['arrive']
                ], cell_format=border_format)
                use_title = False
                count += 1
                total_sum += (value['sum_cleaning'] or 0) * value['arrive']

            if value.get('stay'):
                worksheet.write_row(count, 0, [
                    use_title and index or '',
                    use_title and value['title'] or '',
                    'Отстой ваг-в',
                    '',
                    value['stay'],
                    '', '', '',
                    value['sum_stay'] or 0,
                    (value['sum_stay'] or 0) * value['stay']
                ], cell_format=border_format)
                use_title = False
                count += 1
                total_sum += (value['sum_stay'] or 0) * value['stay']

            if value.get('sum_rent_scale'):
                worksheet.write_row(count, 0, [
                    use_title and index or '',
                    use_title and value['title'] or '',
                    'аренда весов',
                    '', '', '', '', '',
                    value['sum_rent_scale'],
                    value['sum_rent_scale']
                ], cell_format=border_format)
                use_title = False
                count += 1
                total_sum += value['sum_rent_scale']

            if value.get('weighed_count'):
                worksheet.write_row(count, 0, [
                    use_title and index or '',
                    use_title and value['title'] or '',
                    'взвешивание',
                    '', '', '',
                    value['weighed_count'],
                    value['sum_weighing'] or 0,
                    (value['sum_weighing'] or 0) * value['weighed_count']
                ], cell_format=border_format)
                use_title = False
                count += 1
                total_sum += (value['sum_weighing'] or 0) * value['weighed_count']

            if value.get('sum_rent_m'):
                worksheet.write_row(count, 0, [
                    use_title and index or '',
                    use_title and value['title'] or '',
                    'Аренда пом-е',
                    '', '', '', '', '',
                    value['sum_rent_m'],
                    value['sum_rent_m']
                ], cell_format=border_format)
                count += 1
                total_sum += value['sum_rent_m']

            index += 1

        count += 2
        worksheet.write_row(count, 0, [
            '',
            f'ВСЕГО по ЖДО  за {self.MONTH_TITLE.get(month)} {year} г.',
            '', total_arrive, total_stay, '', total_weighed, '', '', ''
        ])
        count += 2
        worksheet.write_row(count, 0, ['', 'Итого доход по жд отделу', '', '', '', '', '', '', '', total_sum])
        count += 1
        worksheet.write_row(count, 0, ['', 'Итого доход по контейнерному двору', '', '', '', '', '', '', '', ''])
        count += 1
        worksheet.write_row(count, 0, [
            '', f'Всего  по ЖД службе за {self.MONTH_TITLE.get(month)} месяц {year} г',
            '', '', '', '', '', '', '', total_sum
        ])
        count += 2

        worksheet.merge_range(
            count, 0, count + 1, 9,
            'Начальник ЖДО                                                                                Иристаев А.',
            bold_format
        )

        workbook.close()
        contents.seek(0)

        return response.raw(
            contents.read(),
            headers={
                'Content-Disposition': 'attachment; filename=report.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
