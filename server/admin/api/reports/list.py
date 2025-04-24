from core.handlers import BaseAPIView


class ReportsView(BaseAPIView):
    template_name = 'admin/reports.html'

    async def get(self, request, user):
        return self.success(request=request, user=user, data={})
