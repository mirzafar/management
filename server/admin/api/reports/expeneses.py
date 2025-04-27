import traceback
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter
from sanic import response

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.roads import ControlRoadsRepository
from data.repository.teplovoz import ControlTeplovozRepository
from utils.strs import StrUtils


class ExpensesReportsView(BaseAPIView):

    async def get(self, request, user):
        started_at = StrUtils.to_str(request.args.get('ex-started-at'))
        stopped_at = StrUtils.to_str(request.args.get('ex-stopped-at'))

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

        teplovoz = await ControlTeplovozRepository.get_teplovoz()

        items = await mongo.expenses.find({
            'dtn': {
                '$gte': started_at,
                '$lte': stopped_at
            }
        }).to_list(length=None)

        contents = BytesIO()
        workbook = xlsxwriter.Workbook(contents)
        worksheet = workbook.add_worksheet('sheet')

        count = 0

        doc_title = f'Оперативное сведение о расходе дизельного топлива тепловозами ЖДО ТОО ИЗО за Февраль месяц 2025 г.'
        worksheet.merge_range(count, 0, count, 8, doc_title)
        count += 2

        i = 0
        worksheet.merge_range(count, i, count + 1, i + 1, 'Сутки', workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'border': 1
        }))
        i += 2

        widths = [10]

        for t in teplovoz.values():
            widths.extend([8, 8, 8])
            worksheet.merge_range(count, i, count, i + 2, t['title'], cell_format=workbook.add_format({
                'align': 'center',
                'text_wrap': True,
                'valign': 'vcenter',
                'border': 1

            }))

            worksheet.write(count + 1, i, 'Приход ДТ ед. изм. В литрах', workbook.add_format({
                'align': 'center',
                'text_wrap': True,
                'valign': 'vcenter',
                'border': 1

            }))
            i += 1

            worksheet.write(count + 1, i, 'Расход суточный ед. изм. В литрах', workbook.add_format({
                'align': 'center',
                'text_wrap': True,
                'valign': 'vcenter',
                'border': 1

            }))
            i += 1

            worksheet.write(count + 1, i, 'Остаток ед. изм. В литрах', workbook.add_format({
                'align': 'center',
                'text_wrap': True,
                'valign': 'vcenter',
                'border': 1

            }))
            i += 1

        worksheet.merge_range(count, i, count + 1, i, 'Расход ДТ в сутки 2 тепловозами ед. изм. В литрах',
                              cell_format=workbook.add_format({
                                  'align': 'center',
                                  'text_wrap': True,
                                  'valign': 'vcenter',
                                  'border': 1

                              }))
        i += 1

        worksheet.merge_range(count, i, count + 1, i, 'Примечание', cell_format=workbook.add_format({
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'border': 1

        }))
        i += 1
        count += 1

        widths.extend([10, 12])
        for i in range(len(widths)):
            worksheet.set_column(i, i, widths[i])

        workbook.close()
        contents.seek(0)

        return response.raw(
            contents.read(),
            headers={
                'Content-Disposition': 'attachment; filename=report.xlsx',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
