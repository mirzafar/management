from core.db import db
from core.handlers import TemplateHTTPView
from utils.ints import IntUtils
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class OrganizationView(TemplateHTTPView):

    async def get(self, request, organization_id):
        organization_id = IntUtils.to_int(organization_id)
        if not organization_id:
            return self.error(message='Отсуствует обязательный параметр "organization_id"')

        organization = await db.fetchrow(
            '''
            SELECT *
            FROM public.organizations
            WHERE id = $1
            ''',
            organization_id,
        ) or {}

        return self.success(request=request, user=None, data={
            'organization': dict(organization)
        })

    async def put(self, request, organization_id):
        organization_id = IntUtils.to_int(organization_id)
        if not organization_id:
            return self.error(message='Отсуствует обязательный параметр "organization_id"')

        title = StrUtils.to_str(request.json.get('title'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        address = StrUtils.to_str(request.json.get('address'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        item = await db.fetchrow(
            '''
            UPDATE public.organizations
            SET title = $2, phone = $3, address = $4
            WHERE id = $1
            RETURNING *
            ''',
            organization_id,
            title,
            phone,
            address
        ) or {}

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, organization_id):
        organization_id = IntUtils.to_int(organization_id)
        if not organization_id:
            return self.error(message='Отсуствует обязательный параметр "organization_id"')

        item = await db.fetchrow(
            '''
            UPDATE public.organizations
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *
            ''',
            organization_id,
        ) or {}

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()
