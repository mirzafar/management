from datetime import datetime

from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreOverheadsView(BaseAPIView):
    template_name = 'admin/store-overheads.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))
        cond, cond_vars = ['is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        if query:
            cond.append('(title ILIKE {same} OR uid ILIKE {})')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        overheads = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                id,
                title,
                description,
                uid,
                date,
                sum,
                is_close
            FROM store.overheads
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM store.overheads
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'overheads': overheads,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        title = StrUtils.to_str(request.json.get('title'))
        description = StrUtils.to_str(request.json.get('description'))
        uid = StrUtils.to_str(request.json.get('uid'))
        date = StrUtils.to_str(request.json.get('date'))
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')

        item_id = await db.fetchval(
            '''
            INSERT INTO store.overheads (title, description, uid, date)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            ''',
            title,
            description,
            uid,
            date or datetime.now().date()
        )

        if not item_id:
            return self.error(message='Операция не выполнена')

        return self.success()


class StoreOverheadView(BaseAPIView):
    template_name = 'admin/store-overhead.html'

    async def get(self, request, user, overhead_id):
        overhead_id = IntUtils.to_int(overhead_id)
        if not overhead_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        overhead = dict(await db.fetchrow(
            '''
            SELECT 
                id,
                title,
                description,
                uid,
                date,
                sum,
                is_close
            FROM store.overheads
            WHERE id = $1
            ORDER BY id DESC
            ''',
            overhead_id,
        ) or {})

        overhead_items = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT
                oi.id,
                CASE WHEN g.id IS NULL 
                    THEN oi.title 
                    ELSE g.title
                END AS title,
                oi.arrival_price,
                oi.sale_price,
                oi.count
            FROM store.overhead_items oi
            LEFT JOIN public.goods g ON g.id = oi.good_id
            WHERE oi.overhead_id = $1
            ORDER BY oi.id DESC
            ''',
            overhead_id
        ))

        overhead.update({
            'sum': 0
        })

        for x in overhead_items:
            if x.get('arrival_price') and x.get('count'):
                overhead['sum'] += (x['arrival_price'] * x['count'])

        return self.success(request=request, user=user, data={
            'overhead': overhead,
            'overhead_items': overhead_items
        })

    async def post(self, request, user, overhead_id):
        overhead_id = IntUtils.to_int(overhead_id)
        if not overhead_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        overhead = await db.fetchrow(
            '''
            SELECT is_close
            FROM store.overheads
            WHERE id = $1
            ''',
            overhead_id
        )

        if not overhead:
            return self.error(message='Данные не найдено')

        if overhead['is_close'] is True:
            return self.error(message='Вынесит изменение запрешено')

        action = StrUtils.to_str(request.json.get('action'))
        if action == 'add_item':
            good_title = StrUtils.to_str(request.json.get('good_title'))
            description = StrUtils.to_str(request.json.get('description'))
            arrival_price = FloatUtils.to_float(request.json.get('arrival_price'))
            sale_price = FloatUtils.to_float(request.json.get('sale_price'))
            count = FloatUtils.to_float(request.json.get('count'))
            good_id = IntUtils.to_int(request.json.get('good_id'))
            category_id = IntUtils.to_int(request.json.get('category_id'))

            if not good_id and not good_title:
                return self.error(message='Выберите товар из списка')

            if not good_id and good_title and not category_id:
                return self.error(message='Выберите категории товара')

            if not arrival_price or arrival_price < 0:
                return self.error(message='Укажите цена прихода')

            if not sale_price or sale_price < 0:
                return self.error(message='Укажите цена продаж')

            if not count:
                return self.error(message='Укажите количество')

            item_id = await db.fetchval(
                '''
                INSERT INTO store.overhead_items
                (title, good_id, description, arrival_price, sale_price, count, overhead_id, category_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                ''',
                good_title,
                good_id,
                description,
                arrival_price,
                sale_price,
                count,
                overhead_id,
                category_id
            )

            if not item_id:
                return self.error(message='Операция не выполнена')

            return self.success()

        elif action == 'remove_item':
            _id = IntUtils.to_int(request.json.get('_id'))
            if not _id:
                return self.error()

            item_id = await db.fetchval(
                '''
                DELETE FROM store.overhead_items 
                WHERE id = $1
                RETURNING id
                ''',
                _id
            )

            if not item_id:
                return self.error(message='Операция не выполнена')

            return self.success()

        elif action == 'close':
            overhead_items = await db.fetch(
                '''
                SELECT id, title, description, good_id, category_id, count, sale_price, arrival_price
                FROM store.overhead_items
                WHERE overhead_id = $1
                ''',
                overhead_id
            )

            if not overhead_items:
                return self.error(message='Добавьте товар')

            item_id = await db.fetchval(
                '''
                UPDATE store.overheads
                SET is_close = TRUE 
                WHERE id = $1
                RETURNING id
                ''',
                overhead_id
            )

            if not item_id:
                return self.error(message='Операция не выполнена')

            summ = 0
            for i in overhead_items:
                if i.get('arrival_price') and i.get('count'):
                    summ += (i['arrival_price'] * i['count'])

                if i['good_id']:
                    await db.execute(
                        '''
                        UPDATE public.goods
                        SET balance = balance + $2, price = $3, last_arrival_price = $4
                        WHERE id = $1
                        ''',
                        i['good_id'],
                        i['count'],
                        i['sale_price'],
                        i['arrival_price'],
                    )
                else:
                    await db.execute(
                        '''
                        WITH inserted_order AS (
                            INSERT INTO public.goods(title, category_id, balance, price, last_arrival_price)
                            VALUES ($2, $3, $4, $5, $6)
                            RETURNING id
                        )
                        UPDATE store.overhead_items
                        SET good_id = (SELECT id FROM inserted_order)
                        WHERE id = $1;
                        ''',
                        i['id'],
                        i['title'],
                        i['category_id'],
                        i['count'],
                        i['sale_price'],
                        i['arrival_price'],
                    )

            if summ:
                await db.execute(
                    '''
                    UPDATE store.overheads
                    SET sum = $2 
                    WHERE id = $1
                    RETURNING id
                    ''',
                    overhead_id,
                    summ
                )

            return self.success()

        return self.error()

    async def put(self, request, user, overhead_id):
        overhead_id = IntUtils.to_int(overhead_id)
        if not overhead_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        title = StrUtils.to_str(request.json.get('title'))
        if not title:
            return self.error(message='Отсуствует обязательный параметры "Название"')

        description = StrUtils.to_str(request.json.get('description'))
        uid = StrUtils.to_str(request.json.get('uid'))
        date = StrUtils.to_str(request.json.get('date'))
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')

        item_id = await db.fetchval(
            '''
            UPDATE store.overheads 
            SET title = $2, description = $3, uid = $4, date = $5
            WHERE id = $1
            RETURNING id
            ''',
            overhead_id,
            title,
            description,
            uid,
            date or datetime.now().date()
        )

        if not item_id:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, overhead_id):
        overhead_id = IntUtils.to_int(overhead_id)
        if not overhead_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        item_id = await db.fetchval(
            '''
            UPDATE store.overheads
            SET is_active = FALSE
            WHERE id = $1
            RETURNING id
            ''',
            overhead_id
        )

        if not item_id:
            return self.error(message='Операция не выполнена')

        return self.success()
