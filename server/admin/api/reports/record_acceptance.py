import calendar
from datetime import datetime
from io import BytesIO

import xlsxwriter
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.companies import ControlCompaniesRepository
from data.repository.states import ControlStatesRepository
from data.repository.types import ControlTypesRepository
from utils.ints import IntUtils
from utils.strs import StrUtils


class RecordAcceptanceReportsView(BaseAPIView):
    MONTH_TITLE = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }

    async def get(self, request, user):
        now = datetime.now()
        month = IntUtils.to_int(request.args.get('r-a-month')) or now.month
        year = IntUtils.to_int(request.args.get('r-a-year')) or now.year
        number = StrUtils.to_str(request.args.get('r-a-number'))
        company_id = StrUtils.to_str(request.args.get('r-a-company-id'))

        companies = await ControlCompaniesRepository.get_companies()
        types = await ControlTypesRepository.get_types()
        states = await ControlStatesRepository.get_states()

        company_title = companies.get(company_id, {}).get('title')
        company_sum_stay = companies.get(company_id, {}).get('sum_stay')

        first_day = datetime(year=year, month=month, day=1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        count = 0

        worksheet.write_row(count, 0, ['Лист №', number])
        count += 1

        doc_title = f'Справка учета принятия и выставления вагонов за {self.MONTH_TITLE.get(month)} месяц {year} года по фирме.'
        worksheet.merge_range(count, 0, count, 5, doc_title)
        worksheet.merge_range(count, 6, count, 7, company_title)
        count += 2

        worksheet.write_row(count, 0, ['переходящий'])
        count += 1

        title_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'border': 1
        })

        # setting title
        titles = [
            dict(name='№', width=3),
            dict(name='Дата принятия', width=15),
            dict(name='№ вагона', width=20),
            dict(name='Пр-е', width=8),
            dict(name='Пр-е', width=8),
            dict(name='Наиманование фирмы', width=30),
            dict(name='Дата выставление', width=15),
            dict(name='Отстой в сутки', width=8),
        ]

        items = await mongo.receipts.find(
            {
                'billed_at': {
                    '$gte': first_day,
                    '$lte': last_day
                },
            }
        ).to_list(length=None)

        old_data = []
        new_data = []
        for item in items:
            if not isinstance(item['arrived_at'], datetime):
                continue

            if first_day <= item['arrived_at'] >= last_day:
                new_data.append(item)
            else:
                old_data.append(item)

        border_format = workbook.add_format({'border': 1})

        old_total = 0
        old_stayed_days = 0

        widths, i = [], 0
        for title in titles:
            worksheet.write(count, i, title['name'], title_format)
            i += 1
            widths.append(title['width'])
        count += 1

        for i in range(len(widths)):
            worksheet.set_column(i, i, widths[i])

        if old_data:
            index = 1
            for d in old_data:
                worksheet.write_row(count, 0, [
                    index,
                    d.get('arrived_at') and datetime.strftime(d.get('arrived_at'), '%d.%m.%Y'),
                    d.get('track_id'),
                    d.get('type_id') and types[d['type_id']]['title'] or '',
                    d.get('state_id') and states[d['state_id']]['title'] or '',
                    company_title,
                    d.get('billed_at') and datetime.strftime(d.get('billed_at'), '%d.%m.%Y'),
                    d.get('stayed_day'),
                ], cell_format=border_format)
                count += 1
                index += 1
                old_total += 1
                old_stayed_days += (d.get('stayed_day') or 0)

        worksheet.write_row(count, 0, [
            '',
            'итого переходяший',
            old_total,
            '',
            '',
            '',
            '',
            old_stayed_days
        ], cell_format=workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'
        }))
        count += 3

        new_total = 0
        new_stayed_days = 0

        i = 0
        for title in titles:
            worksheet.write(count, i, title['name'], title_format)
            i += 1
        count += 1

        if new_data:
            index = 1
            for d in new_data:
                worksheet.write_row(count, 0, [
                    index,
                    d.get('arrived_at') and datetime.strftime(d.get('arrived_at'), '%d.%m.%Y'),
                    d.get('track_id'),
                    d.get('type_id') and types[d['type_id']]['title'] or '',
                    d.get('state_id') and states[d['state_id']]['title'] or '',
                    company_title,
                    d.get('billed_at') and datetime.strftime(d.get('billed_at'), '%d.%m.%Y'),
                    d.get('stayed_day'),
                ], cell_format=border_format)
                count += 1
                index += 1
                new_total += 1
                new_stayed_days += (d.get('stayed_day') or 0)

        worksheet.write_row(count, 0, [
            '',
            'итого текущий',
            new_total,
            '',
            '',
            '',
            '',
            new_stayed_days
        ], cell_format=workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'
        }))
        count += 3

        worksheet.write_row(count, 0, [
            '', '', '', '', '', '', 'итого отстой:', old_stayed_days + new_stayed_days
        ], cell_format=workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'
        }))
        count += 1

        worksheet.write_row(count, 0, [
            '', 'Итого', old_total + new_total, 'вагонов', '', '', 'цена за сутки:', company_sum_stay
        ], cell_format=workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'
        }))
        count += 1

        worksheet.write_row(count, 0, [
            '', '', '', '', '', '', 'итого:', (company_sum_stay or 0) * (old_stayed_days + new_stayed_days)
        ], cell_format=workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter'
        }))
        count += 2

        worksheet.merge_range(
            count, 1, count, 7,
            f'Оплата за оказанные ж.д. услуги отстой вагонов в {self.MONTH_TITLE.get(month)} месяце {year} года {company_title} в пользу'
        )
        count += 1

        worksheet.merge_range(
            count, 1, count, 7,
            f'ТОО «Индустриальная зона Ордабасы составляет в сумме {(company_sum_stay or 0) * (old_stayed_days + new_stayed_days)} согласно выставленной с/фактуры'
        )
        count += 2

        worksheet.merge_range(
            count, 1, count, 3,
            f'Начальник ЖДО'
        )
        worksheet.merge_range(
            count, 5, count, 7,
            f'Иристаев А.Т.'
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
