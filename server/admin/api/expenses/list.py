from datetime import datetime

from core.db import mongo
from core.handlers import BaseAPIView
from data.repository.teplovoz import ControlTeplovozRepository
from utils.floats import FloatUtils
from utils.strs import StrUtils


class ExpensesView(BaseAPIView):
    template_name = 'admin/expenses.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.expenses.find(filters).sort('_id', -1).to_list(length=None)
        expenses = []

        for item in items:
            expenses.append({
                '_id': str(item['_id']),
                'dtn': item.get('dtn') and datetime.strftime(item['dtn'], '%d.%m.%Y'),
                'coming': item.get('coming'),
                'expense': item.get('expense'),
                'teplovoz_id': item.get('teplovoz_id'),
            })
        teplovoz = await ControlTeplovozRepository.get_teplovoz()
        return self.success(request=request, user=user, data={
            'expenses': expenses,
            'teplovoz': teplovoz
        })

    async def post(self, request, user):
        teplovoz_id = StrUtils.to_str(request.json.get('teplovoz_id'))
        dtn = StrUtils.to_str(request.json.get('dtn'))
        coming = FloatUtils.to_float(request.json.get('coming'))
        expense = FloatUtils.to_float(request.json.get('expense'))

        if not coming or not dtn:
            return self.error(message='Отсуствует обязательный параметры "Приход и Уход"')

        if expense and expense > coming:
            return self.error(message='Отсуствует обязательный параметры "Приход и Уход"')

        dtn = datetime.strptime(dtn, '%d.%m.%Y')

        data = {
            'coming': coming,
            'expense': expense,
            'balance': expense and coming - expense or None,
            'dtn': dtn,
            'teplovoz_id': teplovoz_id,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.expenses.insert_one(data)

        if inserted.inserted_id:
            data['id'] = inserted.inserted_id
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'expenses': data
        })
