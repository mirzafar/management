import traceback
from datetime import datetime

from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.floats import FloatUtils
from utils.strs import StrUtils


class ReceiptView(BaseAPIView):
    template_name = 'admin/receipts-item.html'

    async def get(self, request, user, receipt_id):
        receipt_id = StrUtils.to_str(receipt_id)
        if not receipt_id or not ObjectId.is_valid(receipt_id):
            return self.error(message='Отсуствует обязательный параметр "receipt_id"')

        receipt = await mongo.receipts.find_one({'_id': ObjectId(receipt_id)})

        if receipt.get('type_id'):
            _type = await mongo.types.find_one({'_id': ObjectId(receipt['type_id'])})
            if _type:
                receipt['type'] = _type

        if receipt.get('state_id'):
            state = await mongo.states.find_one({'_id': ObjectId(receipt['state_id'])})
            if state:
                receipt['state'] = state

        if receipt.get('company_id'):
            company = await mongo.companies.find_one({'_id': ObjectId(receipt['company_id'])})
            if company:
                receipt['company'] = company

        return self.success(request=request, user=user, data={
            'receipt': receipt
        })

    async def put(self, request, user, receipt_id):
        receipt_id = StrUtils.to_str(receipt_id)
        if not receipt_id or not ObjectId.is_valid(receipt_id):
            return self.error(message='Отсуствует обязательный параметр "receipt_id"')

        arrived_at = StrUtils.to_str(request.json.get('arrived_at'))
        billed_at = StrUtils.to_str(request.json.get('billed_at'))
        before_weight = FloatUtils.to_float(request.json.get('before_weight'))
        after_weight = FloatUtils.to_float(request.json.get('after_weight'))
        description = StrUtils.to_str(request.json.get('description'))
        state_id = StrUtils.to_str(request.json.get('state_id'))
        type_id = StrUtils.to_str(request.json.get('type_id'))

        if arrived_at:
            try:
                arrived_at = datetime.strptime(arrived_at, '%Y-%m-%d')
            except (Exception,):
                traceback.print_exc()

        if not arrived_at:
            arrived_at = datetime.now()

        if billed_at:
            try:
                billed_at = datetime.strptime(billed_at, '%Y-%m-%d')
            except (Exception,):
                traceback.print_exc()

        stayed_day = None
        if arrived_at and billed_at:
            if arrived_at > billed_at:
                return self.error(message='Дата выставление не может быть больше чем дата принятия')
            stayed_day = (billed_at - arrived_at).days

        is_weighed = False
        if before_weight and after_weight:
            is_weighed = True

        if after_weight and before_weight and after_weight > before_weight:
            return self.error(message='Дата выставление не может быть больше чем дата принятия')

        data = {
            'arrived_at': arrived_at,
            'billed_at': billed_at,
            'stayed_day': stayed_day,
            'before_weight': before_weight,
            'after_weight': after_weight,
            'is_weighed': is_weighed,
            'description': description,
            'state_id': state_id,
            'type_id': type_id
        }

        await mongo.receipts.update_one({'_id': ObjectId(receipt_id)}, {'$set': data})

        return self.success(data={
            'receipt': data
        })

    async def delete(self, request, user, receipt_id):
        receipt_id = StrUtils.to_str(receipt_id)
        if not receipt_id or not ObjectId.is_valid(receipt_id):
            return self.error(message='Отсуствует обязательный параметр "receipt_id"')

        await mongo.receipts.update_one({'_id': ObjectId(receipt_id)}, {'$set': {
            'is_active': False
        }})

        return self.success()
