from datetime import datetime

from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
from utils.strs import StrUtils


class ExpenseView(BaseAPIView):

    async def get(self, request, user, expense_id):
        expense_id = StrUtils.to_str(expense_id)
        if not expense_id or not ObjectId.is_valid(expense_id):
            return self.error(message='Отсуствует обязательный параметр "expense_id"')

        expense = await mongo.expenses.find_one({'_id': ObjectId(expense_id)})

        return self.success(request=request, user=user, data={
            'expense': expense
        })

    async def put(self, request, user, expense_id):
        expense_id = StrUtils.to_str(expense_id)
        if not expense_id or not ObjectId.is_valid(expense_id):
            return self.error(message='Отсуствует обязательный параметр "expense_id"')

        dtn = StrUtils.to_str(request.json.get('dtn'))
        coming = FloatUtils.to_float(request.json.get('coming'))
        expense = FloatUtils.to_float(request.json.get('expense'))
        teplovoz_id = StrUtils.to_str(request.json.get('teplovoz_id'))

        if not coming or not dtn:
            return self.error(message='Отсуствует обязательный параметры "Приход и Уход"')

        if expense and expense > coming:
            return self.error(message='Отсуствует обязательный параметры "Приход и Уход"')

        dtn = datetime.strptime(dtn, '%d.%m.%Y')

        await mongo.expenses.update_one({'_id': ObjectId(expense_id)}, {'$set': {
            'dtn': dtn,
            'coming': coming,
            'expense': expense,
            'teplovoz_id': teplovoz_id
        }})

        return self.success()

    async def delete(self, request, user, expense_id):
        expense_id = StrUtils.to_str(expense_id)
        if not expense_id or not ObjectId.is_valid(expense_id):
            return self.error(message='Отсуствует обязательный параметр "expense_id"')

        await mongo.expenses.update_one({'_id': ObjectId(expense_id)}, {'$set': {
            'is_active': False
        }})
        return self.success()
