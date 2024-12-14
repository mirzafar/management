from bson import ObjectId

from core.db import mongo, db
from core.handlers import BaseAPIView
from utils.bools import BoolUtils
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.strs import StrUtils


class StoreIndexView(BaseAPIView):
    template_name = 'admin/sales-index.html'

    async def get(self, request, user):
        cashier_id = IntUtils.to_int(request.args.get('cashier_id'), default=1)

        items = await mongo.cashiers.find({
            'cashier_id': cashier_id
        }).to_list(length=None)

        summ = 0
        for x in items:
            summ += x['sum']

        return self.success(request=request, user=user, data={
            'cashier_id': cashier_id,
            'items': items,
            'sum': summ
        })

    async def post(self, request, user):
        action = StrUtils.to_str(request.json.get('action'))
        if action == 'add':
            good_id = IntUtils.to_int(request.json.get('good_id'))
            if not good_id:
                return self.error(message='Выберите товар')

            count = FloatUtils.to_float(request.json.get('count'))
            if not count:
                return self.error(message='Выберите количество')

            good = await db.fetchrow(
                '''
                SELECT id, balance, price, title
                FROM public.goods
                WHERE id = $1 AND is_active
                ''',
                good_id
            )
            if not good:
                return self.error(message='Выбранный товар не найден')

            if (good['balance'] or 0) == 0:
                return self.error(message=f'В складе не осталось товар')

            if (good['balance'] or 0) < count:
                return self.error(message=f'В складе осталось {good["balance"]}')

            cashier_id = IntUtils.to_int(request.args.get('cashier_id'), default=1)
            if not cashier_id:
                return self.error(message='Выберите кассу')

            await mongo.cashiers.insert_one({
                'cashier_id': cashier_id,
                'good_id': good_id,
                'good_title': good['title'],
                'count': count,
                'price': good['price'],
                'sum': count * good['price'],
            })

            await db.execute(
                '''
                UPDATE public.goods
                SET balance = balance - $2
                WHERE id = $1
                ''',
                good_id,
                count,
            )

            return self.success()

        elif action == 'remove':
            _id = StrUtils.to_str(request.json.get('_id'))
            if ObjectId.is_valid(_id):
                _id = ObjectId(_id)
            else:
                return self.error(message='Операция не выполнена')

            cashier = await mongo.cashiers.find_one_and_delete({'_id': _id})
            if not cashier:
                return self.error()

            await db.execute(
                '''
                UPDATE public.goods
                SET balance = balance + $2
                WHERE id = $1
                ''',
                cashier['good_id'],
                cashier['count'],
            )

            return self.success()

        elif action == 'close':
            cashier_id = IntUtils.to_int(request.args.get('cashier_id'), default=1)
            prev_summ = FloatUtils.to_float(request.json.get('prev_sum'))
            summ = FloatUtils.to_float(request.json.get('sum'))
            pledge = FloatUtils.to_float(request.json.get('pledge'))
            discount = IntUtils.to_int(request.json.get('discount'))
            is_paid = BoolUtils.to_bool(request.json.get('is_paid'), default=False)
            paid_type = StrUtils.to_str(request.json.get('paid_type'))
            if discount > 100 or discount < 0:
                return self.error(message='Скидка не верно')

            if not summ:
                return self.error(message='Вынесите сумму')

            if summ == (100 - (discount or 0)) * prev_summ / 100:
                pass
            else:
                return self.error(message='Систем ошибка')

            if is_paid and pledge:
                return self.error(message='Одновременно оплачен и заклад не возможно')

            order_id = await db.fetchval(
                '''
                INSERT INTO sales.orders (sum, discount, cashier_id, is_paid, pledge, paid_type, total_sum)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                ''',
                prev_summ,
                discount,
                cashier_id,
                is_paid,
                pledge,
                paid_type,
                summ
            )

            cashiers = await mongo.cashiers.find({'cashier_id': cashier_id}).to_list(length=None)
            order_items = []
            for cashier in cashiers:
                order_items.append((
                    cashier['good_id'],
                    cashier['count'],
                    order_id,
                    cashier['sum'],
                    cashier['price']
                ))

                await db.execute(
                    '''
                    UPDATE public.goods
                    SET balance = balance - $2
                    WHERE id = $1
                    ''',
                    cashier['good_id'],
                    cashier['count'],
                )

            await db.executemany(
                '''
                INSERT INTO sales.orders_item (good_id, count, order_id, sum, price)
                VALUES ($1, $2, $3, $4, $5)
                ''',
                order_items
            )
            await mongo.cashiers.delete_many({'cashier_id': cashier_id})

            return self.success()

        return self.error()
