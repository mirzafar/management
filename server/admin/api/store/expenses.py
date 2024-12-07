from datetime import datetime

from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreExpensesView(BaseAPIView):
    template_name = 'admin/store-expenses.html'

    async def get(self, request, user):
        cond, cond_vars = ['e.is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        cond, _ = set_counters(' AND '.join(cond))
        expenses = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                e.id,
                CASE WHEN g.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', g.id,
                        'title', g.title
                    )
                END AS good,
                e.title,
                e.count,
                e.sum,
                e.date
            FROM store.expenses e
            LEFT JOIN public.goods g ON g.id = e.good_id
            WHERE %s
            ORDER BY e.id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))
        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM store.expenses e
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'expenses': expenses,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        good_id = IntUtils.to_int(request.json.get('good_id'))
        title = StrUtils.to_str(request.json.get('title'))
        count = FloatUtils.to_float(request.json.get('count'))
        summ = FloatUtils.to_float(request.json.get('sum'))
        date = StrUtils.to_str(request.json.get('date'))
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')
        else:
            date = datetime.now().date()

        if not good_id and not title:
            return self.error(message='Выберите товар или укажите наименование')

        if count and count <= 0:
            return self.error(message='Отсуствует обязательный параметры "Количество"')

        good = None
        if good_id:
            title = None

            if not count:
                return self.error(message='Отсуствует обязательный параметры "Количество"')

            good = await db.fetchrow(
                '''
                SELECT id, balance, price
                FROM public.goods g
                WHERE g.id = $1
                ''',
                good_id
            )

            if not good:
                return self.error(message='Товар не найден')

            if (good['balance'] or 0) < count:
                return self.error(message=f'В скалде осталось {good["balance"]}')

            if good['price']:
                summ = count * good['price']

        elif not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        if not summ:
            return self.error(message='Отсуствует обязательный параметры "Сумма"')

        item = await db.fetchrow(
            '''
            INSERT INTO store.expenses(good_id, title, count, sum, date, create_by)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *          
            ''',
            good_id,
            title,
            count,
            summ,
            date,
            user['id']
        )

        if good:
            await db.execute(
                '''
                UPDATE public.goods
                SET balance = balance - $2
                WHERE id = $1
                ''',
                good['id'],
                count
            )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()


class StoreExpenseView(BaseAPIView):

    async def delete(self, request, user, expense_id):
        expense_id = IntUtils.to_int(expense_id)
        if not expense_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        expense = await db.fetchrow(
            '''
            SELECT id, count, is_active, good_id
            FROM store.expenses
            WHERE id = $1
            ''',
            expense_id
        )

        if not expense:
            return self.error(message='Не найден')

        if not expense['is_active']:
            return self.error(message='Данный запись уже удален')

        item = await db.fetchrow(
            '''
            UPDATE store.expenses
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *        
            ''',
            expense_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        if expense['good_id'] and expense['count']:
            await db.execute(
                '''
                UPDATE public.goods
                SET balance = balance + $2
                WHERE id = $1
                ''',
                expense['good_id'],
                expense['count']
            )

        return self.success()
