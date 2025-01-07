from core.db import db
from core.handlers import TemplateHTTPView
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class OrganizationsView(TemplateHTTPView):

    async def post(self, request):
        title = StrUtils.to_str(request.json.get('title'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        address = StrUtils.to_str(request.json.get('address'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        item = await db.fetchrow(
            '''
            INSERT INTO public.organizations
            (title, phone, address)
            VALUES ($1, $2, $3)
            RETURNING *
            ''',
            title,
            phone,
            address
        ) or {}

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'organization': dict(item)
        })
