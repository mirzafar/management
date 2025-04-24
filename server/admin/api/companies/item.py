from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
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

    async def post(self, request, user, company_id):
        company_id = StrUtils.to_str(company_id)
        if not company_id or not ObjectId.is_valid(company_id):
            return self.error(message='Отсуствует обязательный параметр "company_id"')
        action = StrUtils.to_str(request.json.get('action'))
        if action == 'add_favorite':
            await mongo.companies.update_one({'_id': ObjectId(company_id)}, {'$set': {
                'is_favorite': True
            }})

            return self.success()

        if action == 'remove_favorite':
            await mongo.companies.update_one({'_id': ObjectId(company_id)}, {'$set': {
                'is_favorite': False
            }})
            return self.success()

        return self.error()

    async def put(self, request, user, company_id):
        company_id = StrUtils.to_str(company_id)
        if not company_id or not ObjectId.is_valid(company_id):
            return self.error(message='Отсуствует обязательный параметр "company_id"')

        title = StrUtils.to_str(request.json.get('title'))
        phone = PhoneNumberUtils.normalize(request.json.get('phone'))
        address = StrUtils.to_str(request.json.get('address'))
        sum_cleaning = FloatUtils.to_float(request.json.get('sum_cleaning'))
        sum_stay = FloatUtils.to_float(request.json.get('sum_stay'))
        sum_weighing = FloatUtils.to_float(request.json.get('sum_weighing'))
        sum_rent_scale = FloatUtils.to_float(request.json.get('sum_rent_scale'))
        sum_rent_m = FloatUtils.to_float(request.json.get('sum_rent_m'))

        if not title:
            return self.error(message='Отсуствует обязательный параметры "Имя"')

        await mongo.companies.update_one({'_id': ObjectId(company_id)}, {'$set': {
            'title': title,
            'phone': phone,
            'address': address,
            'sum_cleaning': sum_cleaning,
            'sum_stay': sum_stay,
            'sum_weighing': sum_weighing,
            'sum_rent_scale': sum_rent_scale,
            'sum_rent_m': sum_rent_m,
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
