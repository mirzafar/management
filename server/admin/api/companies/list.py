from datetime import datetime

from core.db import mongo
from core.handlers import BaseAPIView
from core.pager import Pager
from data.repository.companies import ControlCompaniesRepository
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class CompaniesView(BaseAPIView):
    template_name = 'admin/companies.html'

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 100   ))
        offset = IntUtils.to_int(request.args.get('offset')) or pager.offset

        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.companies.find(filters).skip(offset) \
            .limit(pager.limit) \
            .sort('_id', -1) \
            .to_list(length=None)

        pager.set_total(await mongo.companies.count_documents(filters) or 0)

        return self.success(request=request, user=user, data={
            'companies': items,
            'pager': pager.dict()
        })

    async def post(self, request, user):
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

        data = {
            'title': title,
            'phone': phone,
            'address': address,
            'sum_cleaning': sum_cleaning,
            'sum_stay': sum_stay,
            'sum_weighing': sum_weighing,
            'sum_rent_scale': sum_rent_scale,
            'sum_rent_m': sum_rent_m,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.companies.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
            await ControlCompaniesRepository.delete_cache()

        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'company': data
        })
