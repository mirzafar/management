from datetime import datetime

from bson import ObjectId

from core.db import mongo
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.strs import StrUtils


class TableView(BaseAPIView):
    template_name = 'admin/table.html'

    async def get(self, request, user):
        action = StrUtils.to_str(request.args.get('action'))
        if action == 'get_active_tables':
            history = await mongo.history.find({'is_active': True}).sort('_id', -1).to_list(length=None)
            items = []
            now = datetime.now()
            for item in history:
                if item['type'] == 'with_time':
                    expire = item['time'] - int((now - item['created_at']).total_seconds())
                else:
                    expire = int((now - item['created_at']).total_seconds())

                items.append({
                    'box_id': item['box_id'],
                    'box_title': item['box_title'],
                    'first_score': item['first_score'],
                    'second_score': item['second_score'],
                    'first_player': item['first_player'],
                    'second_player': item['second_player'],
                    'type': item['type'],
                    'created_at': item['created_at'],
                    'expire': expire > 0 and expire or 1
                })

            return self.success(data={'items': items})

        elif action == 'get_summ':
            box_id = IntUtils.to_int(request.args.get('box_id'))
            if not box_id:
                return self.error(message='Отсуствует обязательный параметры "box_id"')

            history = await mongo.history.find_one({'box_id': box_id})
            if not history:
                return self.error(message='Что то не так пошел')

            room = await mongo.rooms.find_one({'id': box_id})

            now = datetime.now()
            if history['type'] == 'with_time':
                expire = history['time']
            else:
                expire = int((now - history['created_at']).total_seconds())

            summ = (room['summ'] or 0) * ((expire or 0) / 60)
            return self.success(data={'expire': expire, 'summ': int(summ)})

        else:
            rooms = await mongo.rooms.find({'is_active': True, 'in_use': False}).to_list(None)
            return self.success(request=request, user=user, data={'rooms': rooms})

    async def post(self, request, user):
        room_id = StrUtils.to_str(request.json.get('room_id'))
        first_player = StrUtils.to_str(request.json.get('first_player'))
        second_player = StrUtils.to_str(request.json.get('second_player'))
        _time = IntUtils.to_int(request.json.get('time'), default=0)

        if not room_id or not ObjectId.is_valid(room_id):
            return self.error(message='Отсуствует обязательный параметры "room_id"')

        room = await mongo.rooms.find_one({'_id': ObjectId(room_id), 'in_use': False, 'is_active': True})
        if not room:
            return self.error(message='Стол не найден или пока занят')

        data = {
            'room_id': room_id,
            'box_title': room['title'],
            'box_id': room['id'],
            'first_player': first_player,
            'second_player': second_player,
            'first_score': 0,
            'second_score': 0,
            'type': _time and 'with_time' or 'no_time',
            'time': _time * 60,
            'is_finish': False,
            'is_paid': False,
            'is_active': True,
            'created_at': datetime.now()
        }

        inserted = await mongo.history.insert_one(data)

        if inserted.inserted_id:
            await mongo.rooms.update_one({'_id': ObjectId(room_id)}, {'$set': {'in_use': True}})
            data['id'] = inserted.inserted_id
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'data': data
        })

    async def put(self, request, user):
        action = StrUtils.to_str(request.json.get('action'))
        box_id = IntUtils.to_int(request.json.get('box_id'))
        if not box_id:
            return self.error(message='Отсуствует обязательный параметры "box_id"')

        if action == 'change_score':
            player = StrUtils.to_str(request.json.get('player'))
            value = IntUtils.to_int(request.json.get('value'), default=0)

            update_data = {}

            if player == 'first':
                update_data['first_score'] = value
            elif player == 'second':
                update_data['second_score'] = value
            else:
                return self.error(message='Отсуствует обязательный параметры "player"')

            await mongo.history.update_one({'box_id': box_id}, {'$set': update_data})

        elif action == 'close':
            expire = IntUtils.to_int(request.json.get('expire'), default=0)
            summ = IntUtils.to_int(request.json.get('summ'), default=0)

            if not expire or not summ:
                return self.error(message='Операция не выполнена')

            box = await mongo.history.find_one({'box_id': box_id})
            if not box:
                return self.error(message='Операция не выполнена')

            await mongo.rooms.update_one({'id': box_id}, {'$set': {'in_use': False}})
            await mongo.history.delete_one({'box_id': box_id})
            await mongo.orders.insert_one({
                'box_id': box_id,
                'expire': expire,
                'summ': summ,
                'first_player': box['first_player'],
                'second_player': box['second_player'],
                'first_score': box['first_score'],
                'second_score': box['second_score'],
                'time_start': box['created_at'],
                'created_at': datetime.now()
            })

        return self.success(data={})
