import calendar
from datetime import datetime
from io import BytesIO

import xlsxwriter
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.companies import ControlCompaniesRepository
from utils.floats import FloatUtils
from utils.strs import StrUtils


class InvoiceCompanyReportsView(BaseAPIView):
    MONTH_TITLE = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }

    async def get(self, request, user):
        now = datetime.now()

        company_id = StrUtils.to_str(request.args.get('ic-company-id'))
        write_dtn = StrUtils.to_str(request.args.get('ic-write-dtn'))
        contracts_dtn = StrUtils.to_str(request.args.get('ic-contract-dtn'))
        month = StrUtils.to_str(request.args.get('ic-month')) or now.month
        year = StrUtils.to_str(request.args.get('ic-year')) or now.year

        first_day = datetime(year=year, month=month, day=1)
        last_day = datetime(year, month, calendar.monthrange(year, month)[1])

        if write_dtn:
            write_dtn = datetime.strptime(write_dtn, '%d.%m.%Y').strftime('%d.%m.%Y')
        else:
            write_dtn = datetime.strftime(now, '%d.%m.%Y')

        if contracts_dtn:
            contracts_dtn = datetime.strptime(contracts_dtn, '%d.%m.%Y').strftime('%d.%m.%Y')
        else:
            contracts_dtn = datetime.strftime(now, '%d.%m.%Y')

        companies = await ControlCompaniesRepository.get_companies()

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        worksheet.write(0, 3, 'АКТ', workbook.add_format({'align': 'center'}))
        worksheet.merge_range(1, 0, 1, 7, f'Выполненной работы от {write_dtn} года ТОО «Индустриальная зона Ордабасы»')
        worksheet.merge_range(2, 0, 2, 7,
                              f'Ниязметов Н.Ю. и директор ТОО «АЗИЗИ КЗ» Азизи А.А., составили настоящий акт,')
        worksheet.merge_range(3, 0, 3, 7,
                              f'в том, что согласно договора №23-25 Ж от {contracts_dtn} г. на п/пути ТОО «Индустриальная зона')
        worksheet.merge_range(4, 0, 4, 7,
                              f'Ордабасы» на отстое находились вагоны {companies.get(company_id, {}).get("title", "")} в {self.MONTH_TITLE.get(month)} месяце {year} года в ')

        worksheet.merge_range(5, 0, 5, 7,
                              f'следующем порядке: ')

        total = await mongo.lagging_receipts.count_documents(
            {
                'dtn': {
                    '$gte': first_day,
                    '$lte': last_day
                },
                'event': 'stay',
                'company_id': company_id
            }
        ) or 0

        worksheet.write(7, 0, f'1. Предоставление подъездного пути для проезда подвижного состава при условии')
        worksheet.write(8, 0, f'отсутствия конкурентного п/пути')
        worksheet.write_row(9, 1, ['в', 'км', 'в/км', 'тенге'], workbook.add_format({'align': 'center', 'border': 1}))
        ic_a_metr = FloatUtils.to_float(request.args.get('ic-a-metr')) or 0
        ic_a_chas = FloatUtils.to_float(request.args.get('ic-a-chas')) or 0
        total_a = ic_a_metr * ic_a_chas
        worksheet.write_row(10, 1, [total, ic_a_metr, ic_a_chas, total_a],
                            workbook.add_format({'align': 'center', 'border': 1}))
        worksheet.write(12, 0, f'2. Предоставление подъездного пути для маневровых работ')
        worksheet.write_row(13, 1, ['в', 'час', 'в/час', 'тенге'],
                            workbook.add_format({'align': 'center', 'border': 1}))
        ic_b_chas = FloatUtils.to_float(request.args.get('ic-b-chas')) or 0
        ic_b_v = FloatUtils.to_float(request.args.get('ic-b-v')) or 0
        total_b = ic_b_chas * ic_b_v
        worksheet.write_row(14, 1, [total, ic_b_chas, ic_b_v, total_b],
                            workbook.add_format({'align': 'center', 'border': 1}))
        worksheet.write(16, 0, f'3. Предоставления услуги локомотивной тяги')
        ic_c_chas = FloatUtils.to_float(request.args.get('ic-c-chas')) or 0
        ic_c_v = FloatUtils.to_float(request.args.get('ic-c-v')) or 0
        total_c = ic_c_chas * ic_c_v
        worksheet.write_row(17, 1, ['в', 'час', 'тенге', 'тенге'],
                            workbook.add_format({'align': 'center', 'border': 1}))
        worksheet.write_row(18, 1, [total, ic_c_chas, ic_c_v, total_c],
                            workbook.add_format({'align': 'center', 'border': 1}))

        worksheet.write(20, 1, 'ИТОГО:', workbook.add_format({'align': 'center', 'bold': True}))
        worksheet.write(20, 4, total_c + total_b + total_a, workbook.add_format({'align': 'center', 'bold': True}))

        worksheet.merge_range(21, 0, 21, 7,
                              f'Оплата  за оказанные ж.д. услуги в {self.MONTH_TITLE.get(month)}  месяце {year} года')
        worksheet.merge_range(22, 0, 22, 7,
                              f'{companies.get(company_id, {}).get("title")} в пользу  ТОО «Индустриальная зона Ордабасы')
        worksheet.merge_range(23, 0, 23, 7,
                              f'составляет в сумме {total_c + total_b + total_a} тенге согласно выставленной с/фактуры.')
        worksheet.write(25, 0, f'Начальник ЖДО:')
        worksheet.write(25, 4, f'Иристаев А.Т.')

        worksheet.write(27, 0, f'Начальники смены:')
        worksheet.write(27, 4, f'Ниязметов.Н.Ю.')
        worksheet.write(28, 4, f'Саттарханов Н')
        worksheet.write(30, 0, f'Директор')
        worksheet.write(31, 0, f'{companies.get(company_id, {}).get("title", "")}')
        worksheet.write(31, 4, f'{companies.get(company_id, {}).get("manager", "")}')

        workbook.close()
        contents.seek(0)

        return response.raw(
            contents.read(),
            headers={
                'Content-Disposition': 'attachment; filename=report.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
