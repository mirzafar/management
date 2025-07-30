from core.handlers import BaseAPIView


class AssistantsView(BaseAPIView):
    template_name = 'admin/assistants.html'

    async def get(self, request, user):
        return self.success(request=request, user=user, data={})
