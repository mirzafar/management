from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.bools import BoolUtils
from utils.floats import FloatUtils
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class StoreVisitsView(BaseAPIView):
    template_name = 'admin/store-visits.html'

    async def get(self, request, user):
        cond, cond_vars = ['v.is_active'], []

        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 20))

        cond, _ = set_counters(' AND '.join(cond))
        visits = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT 
                v.id, 
                v.title, 
                v.description, 
                CASE WHEN g.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', g.id,
                        'title', g.title
                    )
                END AS good,
                CASE WHEN c.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', c.id,
                        'first_name', c.first_name,
                        'last_name', c.last_name
                    )
                END AS client,
                v.is_our,
                CASE WHEN r.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', r.id,
                        'title', r.title
                    )
                END AS reason,
                v.count,
                v.sum,
                v.created_at,
                v.is_paid
            FROM store.visits v
            LEFT JOIN public.goods g ON g.id = v.good_id
            LEFT JOIN store.reasons r ON r.id = v.reason_id
            LEFT JOIN public.clients c ON c.id = v.client_id
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))
        pager.set_total(await db.fetchval(
            '''
            SELECT count(*)
            FROM store.visits v
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0)

        return self.success(request=request, user=user, data={
            'visits': visits,
            'pager': pager.dict()
        })

    async def post(self, request, user):
        client_id = IntUtils.to_int(request.json.get('client_id'))
        if not client_id:
            return self.error(message='Отсуствует обязательный параметры "Клиент"')

        good_id = IntUtils.to_int(request.json.get('good_id'))
        title = StrUtils.to_str(request.json.get('title'))
        if not good_id and not title:
            return self.error(message='Отсуствует обязательный параметры "Название" или Выберите товар')

        is_our = BoolUtils.to_bool(request.json.get('is_our'), False)
        if is_our is False and not good_id:
            return self.error(message='Выберите товар при отсутствие "C собой"')

        reason_id = IntUtils.to_int(request.json.get('reason_id'))
        if not reason_id:
            return self.error(message='Отсуствует обязательный параметры "Вид услуги"')

        count = FloatUtils.to_float(request.json.get('count'))
        if not count or count <= 0:
            return self.error(message='Отсуствует обязательный параметры "Количество"')

        sum_reason = FloatUtils.to_float(request.json.get('sum_reason'))
        sum_good = FloatUtils.to_float(request.json.get('sum_good'))
        if (sum_reason and sum_reason < 0) or not sum_reason:
            return self.error(message='Отсуствует обязательный параметры "Сумма услуги"')

        if (sum_good and sum_good < 0) or (is_our is False and not sum_good):
            return self.error(message='Отсуствует обязательный параметры "Сумма товара"')

        is_paid = BoolUtils.to_bool(request.json.get('is_paid'), False)
        pledged_sum = FloatUtils.to_float(request.json.get('pledged_sum'))
        description = StrUtils.to_str(request.json.get('description'))

        if pledged_sum and is_paid:
            return self.error('Одновренно заклад и оплачен не может быть')

        good = None
        if good_id and is_our is False:
            good = await db.fetchrow(
                '''
                SELECT id, price, balance
                FROM public.goods
                WHERE id = $1 AND is_active
                ''',
                good_id
            )

            if not good:
                return self.error(message='Данный товар не найден в складе')

            if good['balance'] <= 0 or good['balance'] <= count:
                return self.error(message=f'В складе осталось {good["balance"]} остаток')

        item = await db.fetchrow(
            '''
            INSERT INTO store.visits(title, description, good_id, is_our, reason_id, count, sum, client_id, is_paid, pledged_sum)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING *          
            ''',
            title,
            description,
            good_id,
            is_our,
            reason_id,
            count,
            sum_reason + sum_good,
            client_id,
            is_paid,
            pledged_sum
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


class StoreVisitView(BaseAPIView):
    async def get(self, request, user, visit_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        visit = await db.fetchrow(
            '''
            SELECT 
                v.id, 
                v.title, 
                v.description, 
                CASE WHEN g.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', g.id,
                        'title', g.title
                    )
                END AS good,
                v.is_our,
                CASE WHEN r.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', r.id,
                        'title', r.title
                    )
                END AS reason,
                CASE WHEN c.id IS NOT NULL 
                    THEN JSONB_BUILD_OBJECT(
                        'id', c.id,
                        'first_name', c.first_name,
                        'last_name', c.last_name
                    )
                END AS client,
                v.count,
                v.sum,
                v.created_at,
                v.pledged_sum,
                v.is_paid
            FROM store.visits v
            LEFT JOIN public.goods g ON g.id = v.good_id
            LEFT JOIN store.reasons r ON r.id = v.reason_id
            LEFT JOIN public.clients c ON c.id = v.client_id
            WHERE v.id = $1
            ''',
            visit_id
        ) or {}

        return self.success(request=request, user=user, data={
            'visit': dict(visit)
        })

    async def put(self, request, user, visit_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        visit = await db.fetchrow(
            '''
            SELECT is_paid, sum
            FROM store.visits
            WHERE id = $1
            ''',
            visit_id
        )

        if not visit:
            return self.error(message='Не найден')

        summ = FloatUtils.to_float(request.json.get('sum'))
        if not summ or summ <= 0:
            return self.error(message='Отсуствует обязательный параметры "Сумма"')

        is_paid = BoolUtils.to_bool(request.json.get('is_paid'), False)
        if (visit['is_paid'] and summ != visit['sum']) or (visit['is_paid'] and not is_paid):
            return self.error(message='Сумма не редактируется так как услуга уже оплачен')

        description = StrUtils.to_str(request.json.get('description'))

        item = await db.fetchrow(
            '''
            UPDATE store.visits
            SET is_paid = $2, description = $3, sum = $4
            WHERE id = $1
            RETURNING id
            ''',
            visit_id,
            is_paid,
            description,
            summ
        )

        if not item:
            return self.error(message='Операция не выполнена')

        return self.success()

    async def delete(self, request, user, visit_id):
        visit_id = IntUtils.to_int(visit_id)
        if not visit_id:
            return self.error(message='Отсуствует обязательный параметры "ID"')

        visit = await db.fetchrow(
            '''
            SELECT id, count, is_active, good_id, is_our
            FROM store.visits
            WHERE id = $1
            ''',
            visit_id
        )

        if not visit:
            return self.error(message='Не найден')

        if not visit['is_active']:
            return self.error(message='Данный запись уже удален')

        item = await db.fetchrow(
            '''
            UPDATE store.visits
            SET is_active = FALSE
            WHERE id = $1
            RETURNING *        
            ''',
            visit_id
        )

        if not item:
            return self.error(message='Операция не выполнена')

        if visit['good_id'] and visit['count'] and not visit['is_our']:
            await db.execute(
                '''
                UPDATE public.goods
                SET balance = balance + $2
                WHERE id = $1
                ''',
                visit['good_id'],
                visit['count']
            )

        return self.success()
