import calendar
from datetime import datetime, date

from core.handlers import BaseAPIView
from data.repository.companies import ControlCompaniesRepository


class ReportsView(BaseAPIView):
    template_name = 'admin/reports.html'

    async def get(self, request, user):
        companies = await ControlCompaniesRepository.get_companies()
        now = datetime.now()

        first_day = date(year=now.year, month=now.month, day=1)
        last_day = date(now.year, now.month, calendar.monthrange(now.year, now.month)[1])
        return self.success(request=request, user=user, data={
            'companies': companies,
            'first_day': first_day,
            'last_day': last_day,
            'month': now.month,
            'year': now.year,
        })
