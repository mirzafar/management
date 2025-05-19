import traceback
from datetime import datetime

import ujson
from pymongo import ReturnDocument
from sanic import response
from sanic.views import HTTPMethodView

from core import i18n
from core.cache import cache
from core.db import mongo
from data.repository.catalog import on_catalog, on_selected
from data.repository.goods import ControlGoodsRepository


# data = {
#     'update_id': 929199204,
#     'message': {
#         'message_id': 136300,
#         'from': {'id': 702160070, 'is_bot': False, 'first_name': 'Mirzafar',
#                  'username': 'm1rzafar', 'language_code': 'en'},
#         'chat': {'id': 702160070, 'first_name': 'Mirzafar', 'username': 'm1rzafar',
#                  'type': 'private'}, 'date': 1747564438, 'text': 'dawd'
#     }
# }

# callback = {
#     'update_id': 238283914,
#     'callback_query': {
#         'id': '3015754537387908053',
#         'from': {
#             'id': 702160070, 'is_bot': False,
#             'first_name': 'Mirzafar', 'username': 'm1rzafar',
#             'language_code': 'en'},
#         'message': {'message_id': 94,
#                     'from': {
#                         'id': 7166723089,
#                         'is_bot': True,
#                         'first_name': 'ХлебоДоставка',
#                         'username': 'Bread_delivery_bot'},
#                     'chat': {
#                         'id': 702160070,
#                         'first_name': 'Mirzafar',
#                         'username': 'm1rzafar',
#                         'type': 'private'},
#                     'date': 1747586030,
#                     'text': 'Карзинка пусто. Для добавление товара нажмите кнопку "✅Bыбрать продукт"',
#                     'reply_markup': {
#                         'inline_keyboard': [
#                             [{
#                                 'text': '✅Bыбрать продукт',
#                                 'callback_data': 'chooseGoods'}]]}},
#         'chat_instance': '-8321419619944981968', 'data': 'chooseGoods'}}

def validate_phone(value: str):
    if value.startswith('7') or value.startswith('8'):
        if len(value) == 11:
            return value
        else:
            return None

    elif value.startswith('+'):
        if len(value) == 12:
            return value
        else:
            return None

    return None


class TelegramWebhookView(HTTPMethodView):
    async def post(self, request):
        try:
            data = request.json or {}
            print(f'TelegramWebhookView.post: {data}')

            message = data.get('message')
            callback_data = data.get('callback_query', {}).get('data')

            text, chat_id = None, None

            if message:
                chat_id = message.get('chat', {}).get('id')
            elif data.get('callback_query', {}).get('message', {}).get('chat', {}).get('id'):
                chat_id = data['callback_query']['message']['chat']['id']

            if message and message.get('text') == '/start':
                await cache.delete(
                    f'bread:selectGood:{chat_id}',
                    f'bread:{chat_id}:finish:state'
                )
                return response.json({
                    'method': 'sendMessage',
                    'chat_id': chat_id,
                    'text': i18n.GREETING_BOT,
                    'reply_markup': {
                        'keyboard': [
                            ['\u2063📔Каталог'],
                            ['\u2062📦Заказать'],
                            ['\u2062🗃Мои заказы'],
                        ],
                        'resize_keyboard': True,
                        'one_time_keyboard': True,
                        'selective': True
                    }
                })

            if message and message.get('text'):
                text = message['text']

            elif message and message.get('caption'):
                text = message['caption']

            if not text and not callback_data:
                return response.json({
                    'method': 'sendMessage',
                    'chat_id': chat_id,
                    'text': i18n.PLEASE_WRITE
                })

            if f_state := await cache.get(f'bread:{chat_id}:finish:state'):
                if f_state == 'address':
                    if text:
                        await cache.set(f'bread:{chat_id}:finish:state', 'phone')
                        await cache.set(f'bread:{chat_id}:address', text)
                        return response.json({
                            'method': 'sendMessage',
                            'chat_id': chat_id,
                            'text': 'Пожалуйста введите номер телефона',
                        })
                    else:
                        return response.json({
                            'method': 'sendMessage',
                            'chat_id': chat_id,
                            'text': 'Пожалуйста введите правильный адрес',
                        })

                elif f_state == 'phone':
                    if text and validate_phone(text):
                        basket = await cache.get(f'bread:{chat_id}:basket')
                        address = await cache.get(f'bread:{chat_id}:address')
                        await cache.delete(
                            f'bread:{chat_id}:finish:state',
                            f'bread:{chat_id}:basket',
                            f'bread:selectGood:{chat_id}',
                            f'bread:{chat_id}:address'
                        )
                        counter = await mongo.counters.find_one_and_update(
                            filter={'collection': 'orders'},
                            update={'$inc': {'seq': 1}},
                            upsert=True,
                            return_document=ReturnDocument.AFTER
                        )
                        await mongo.orders.insert_one({
                            'created_at': datetime.now(),
                            'id': counter['seq'],
                            'chat_id': chat_id,
                            'items': basket and ujson.loads(basket) or None,
                            'address': address,
                            'phone': text
                        })
                        return response.json({
                            'method': 'sendMessage',
                            'chat_id': chat_id,
                            'text': 'Ваш заказ усепшно зарегистирован',
                            'reply_markup': {
                                'keyboard': [
                                    ['\u2063📔Каталог'],
                                    ['\u2062📦Заказать'],
                                    ['\u2062🗃Мои заказы'],
                                ],
                                'resize_keyboard': True,
                                'one_time_keyboard': True,
                                'selective': True
                            }
                        })
                    else:
                        return response.json({
                            'method': 'sendMessage',
                            'chat_id': chat_id,
                            'text': 'Пожалуйста введите правильный номер телефона',
                        })

            if good_id := await cache.get(f'bread:selectGood:{chat_id}'):
                goods = await ControlGoodsRepository.get_goods()
                good = goods[good_id]
                count = text and text.isdigit() and int(text)
                if count and count > 0:
                    basket = await cache.get(f'bread:{chat_id}:basket')
                    if basket:
                        basket = ujson.loads(basket)
                    else:
                        basket = []

                    basket.append({'title': good['title'], 'count': count, 'sum': count * (good['price'] or 0)})

                    inline_keyboard = [[{'text': '✅Bыбрать продукт', 'callback_data': 'chooseGoods'}],
                                       [{'text': '🗑Очистить карзинку', 'callback_data': 'clearBasket'}],
                                       [{'text': '💳Оформить заказ', 'callback_data': 'doneBasket'}]]

                    response_text = 'Товары в корзине:\n\n'
                    total_sum = 0
                    for g in basket:
                        response_text += f'{g["title"]}: {g["count"]}\n'
                        if g.get('sum'):
                            total_sum += g['sum']

                    response_text += f'\n\nК оплате: {total_sum}'

                    await cache.delete(f'bread:selectGood:{chat_id}')
                    await cache.set(f'bread:{chat_id}:basket', ujson.dumps(basket))

                    return response.json({
                        'method': 'sendMessage',
                        'chat_id': chat_id,
                        'text': response_text,
                        'reply_markup': {
                            'inline_keyboard': inline_keyboard
                        }
                    })

                else:
                    return response.json({
                        'method': 'sendMessage',
                        'chat_id': chat_id,
                        'parse_mode': 'Markdown',
                        'text': f'Выбрали *{good["title"]}*. Напишите количество'
                    })

            if text and text.startswith('\u2063'):
                return response.json(await on_catalog(chat_id))

            if text and text.startswith('\u2062'):
                basket = await cache.get(f'bread:{chat_id}:basket')
                if basket:
                    basket = ujson.loads(basket)

                inline_keyboard = [[{'text': '✅Bыбрать продукт', 'callback_data': 'chooseGoods'}]]
                if basket:
                    response_text = 'Товары в корзине:\n\n'
                    inline_keyboard.extend([
                        [{'text': '🗑Очистить карзинку', 'callback_data': 'clearBasket'}],
                        [{'text': '💳Оформить заказ', 'callback_data': 'doneBasket'}],
                    ])
                    for g in basket:
                        response_text += f'{g["title"]}: {g["count"]}\n'
                else:
                    response_text = 'Карзинка пусто. Для добавление товара нажмите кнопку "✅Bыбрать продукт"'

                return response.json({
                    'method': 'sendMessage',
                    'chat_id': chat_id,
                    'text': response_text,
                    'reply_markup': {
                        'inline_keyboard': inline_keyboard
                    }
                })

            if callback_data and callback_data == 'chooseGoods':
                goods = await ControlGoodsRepository.get_goods()

                return response.json({
                    'method': 'editMessageText',
                    'message_id': data.get('callback_query', {}).get('message', {}).get('message_id') or None,
                    'chat_id': chat_id,
                    'text': 'Выберите товар',
                    'reply_markup': {
                        'inline_keyboard': [
                            [{'text': c['title'], 'callback_data': f'selectGood:{c["id"]}'}] for c in goods.values()
                        ]
                    }
                })

            elif callback_data and callback_data.startswith('selectGood'):
                goods = await ControlGoodsRepository.get_goods()
                good = goods[callback_data.split(':')[1]]
                await cache.set(f'bread:selectGood:{chat_id}', good['id'])
                message_id = data.get('callback_query', {}).get('message', {}).get('message_id')
                return response.json({
                    'method': message_id and 'editMessageText' or 'sendMessage',
                    'message_id': message_id,
                    'chat_id': chat_id,
                    'parse_mode': 'Markdown',
                    'text': f'Выбрали *{good["title"]}*. Напишите количество'
                })

            elif callback_data and callback_data.startswith('clearBasket'):
                await cache.delete(f'bread:{chat_id}:basket', f'bread:selectGood:{chat_id}')
                message_id = data.get('callback_query', {}).get('message', {}).get('message_id')
                return response.json({
                    'method': message_id and 'editMessageText' or 'sendMessage',
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'text': 'Карзинка пусто. Для добавление товара нажмите кнопку "✅Bыбрать продукт"',
                    'reply_markup': {
                        'inline_keyboard': [[{'text': '✅Bыбрать продукт', 'callback_data': 'chooseGoods'}]]
                    }
                })

            elif callback_data and callback_data.startswith('doneBasket'):
                await cache.delete(f'bread:selectGood:{chat_id}')
                await cache.set(f'bread:{chat_id}:finish:state', 'address')
                message_id = data.get('callback_query', {}).get('message', {}).get('message_id')
                return response.json({
                    'method': message_id and 'editMessageText' or 'sendMessage',
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'text': 'Пожалуйста введите адрес',
                })

            elif callback_data and callback_data.startswith('catalog:Select'):
                return response.json(await on_selected(chat_id, callback_data.split(':')[2]))

        except (Exception,):
            traceback.print_exc()

        return response.json({})
