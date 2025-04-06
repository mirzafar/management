from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class CompanyView(BaseAPIView):
    template_name = 'admin/companies-item.html'

    async def get(self, request, user, company_id):
        company_id = StrUtils.to_str(company_id)
        if not company_id or not ObjectId.is_valid(company_id):
            return self.error(message='Отсуствует обязательный параметр "company_id"')

        company = await mongo.companies.find_one({'_id': ObjectId(company_id)})

        return self.success(request=request, user=user, data={
            'company': company
        })

    async def put(self, request, user, company_id):
        company_id = StrUtils.to_str(company_id)
        if not company_id or not ObjectId.is_valid(company_id):
            return self.error(message='Отсуствует обязательный параметр "company_id"')

        title = StrUtils.to_str(request.json.get('title'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        address = StrUtils.to_str(request.json.get('address'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        await mongo.companies.update_one({'_id': ObjectId(company_id)}, {'$set': {
            'title': title,
            'phone': phone,
            'address': address
        }})

        return self.success()

    async def delete(self, request, user, company_id):
        company_id = StrUtils.to_str(company_id)
        if not company_id or not ObjectId.is_valid(company_id):
            return self.error(message='Отсуствует обязательный параметр "company_id"')

        await mongo.companies.update_one({'_id': ObjectId(company_id)}, {'$set': {
            'is_active': False
        }})

        return self.success()
