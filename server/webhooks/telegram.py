import random

from sanic import response
from sanic.views import HTTPMethodView

from clients.telegram import tgclient
from core.db import db
from core.hasher import password_to_hash
from utils.dicts import DictUtils
from utils.strs import StrUtils


class TelegramWebhookHandler(HTTPMethodView):
    async def get(self, request):
        return response.json({})

    async def post(self, request):
        data = request.json

        print(f'telegram_message: {data}')

        message = DictUtils.as_dict(data.get('message'))

        if message:
            chat_id = StrUtils.to_str(message.get('chat', {}).get('id'))
            sender = message.get('from', {})
            customer = await db.fetchrow(
                '''
                SELECT u.id, u.username
                FROM public.accounts a
                LEFT JOIN users u on u.id = a.user_id
                WHERE channel = $1 AND uid = $2
                ''',
                'tg',
                chat_id
            )
        else:
            return response.json({})

        if not customer:
            customer = await db.fetchrow(
                '''
                INSERT INTO public.users(last_name, username)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                RETURNING id, username
                ''',
                sender['first_name'],
                sender['username']
            )

            if not customer:
                return response.json({})

            account = await db.fetchrow(
                '''
                INSERT INTO public.accounts(uid, channel, user_id)
                VALUES ($1, $2, $3)
                RETURNING *
                ''',
                chat_id,
                'tg',
                customer['id']
            )

            if not account:
                return response.json({})

        if message and message.get('text') == '/start':
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'Выберите из меню, чем я могу Вам помочь',
                    'disable_web_page_preview': True,
                    'parse_mode': 'HTML',
                    'reply_markup': {
                        'remove_keyboard': True,
                        'keyboard': [
                            [{'text': '\u2065Получить код подверждение'}]
                        ],
                        'resize_keyboard': True,
                    }
                }
            )

            return response.json({})

        text = None
        success = False
        if message and message.get('text'):
            text = message['text']

        if text:
            if text.startswith('\u2065'):
                code = random.randint(pow(10, 5), pow(10, 6) - 1)
                await db.fetchrow(
                    '''
                    UPDATE public.users
                    SET password = $2
                    WHERE id = $1
                    ''',
                    customer['id'],
                    password_to_hash(code)
                )

                success = True
                await tgclient.api_call(
                    payload={
                        'chat_id': chat_id,
                        'text': f'Ваш профиль:\nлогин=*{customer["username"]}*\nпароль=*{code}*',
                        'parse_mode': 'markdown',
                    }
                )
        if success is False:
            await tgclient.api_call(
                payload={
                    'chat_id': chat_id,
                    'text': 'В системе ничего не найдено',
                }
            )

        return response.json({})
