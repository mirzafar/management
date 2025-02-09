import random
from datetime import datetime

from bson import ObjectId
from sanic import response

from core.db import db, mongo
from core.handlers import TemplateHTTPView, auth, BaseAPIView
from core.hasher import password_to_hash
from core.session import session
from utils.lists import ListUtils
from utils.phones import PhoneNumberUtils
from utils.strs import StrUtils


class LoginAdminView(TemplateHTTPView):
    template_name = 'auth/login.html'

    async def get(self, request):
        await auth.logout(request)
        return self.success(request=request)

    async def post(self, request):
        if not request.json:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр(ы)'
            })

        username = StrUtils.to_str(request.json.get('username'))
        password = StrUtils.to_str(request.json.get('password'))

        if not username:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр "username: str"'
            })

        if not password:
            return response.json({
                '_success': False,
                'message': 'Отсуствует обязательный параметр "password: str"'
            })

        user = await db.fetchrow(
            '''
            SELECT id, username, is_blocked, is_active
            FROM public.users u
            WHERE u.username = $1 AND u.password = $2
            ''',
            username,
            password_to_hash(password=password)
        )

        if user:
            user = dict(user)
        else:
            return response.json({
                '_success': False,
                'message': 'Пользователь не найден(-o, -а) в системе'
            })

        if user['is_blocked']:
            return response.json({
                '_success': False,
                'message': 'Пользователь заблокирован(-о, -а) в системе'
            })

        if not user['is_active']:
            return response.json({
                '_success': False,
                'message': 'Пользователь удален(-о, -а) из системы'
            })

        token = await session.create_session(request, user['id'])
        await auth.login(request, user, token)

        return response.json({
            '_success': True,
            'url': '/api/',
            'token': token,
            'user_id': user['id'],
        })


class LogoutAdminView(BaseAPIView):
    async def get(self, request, user):
        return await auth.logout(request)


class RegisterAdminView(TemplateHTTPView):
    async def post(self, request):
        return response.json({
            '_success': True
        })


class OTPAdminView(TemplateHTTPView):
    async def get(self, request):
        otp = await mongo.opt.find({
            'is_active': True
        }).to_list(length=None) or []

        return response.json({
            '_success': True,
            'otp': [{
                'id': str(i['_id']),
                'phone': i['phone'],
                'code': i['code']
            } for i in otp]
        })

    async def post(self, request):
        action = request.json.get('action')

        if action == 'send':
            phone = PhoneNumberUtils.normalize(request.json.get('phone'))
            if not phone:
                return response.json({
                    '_success': False,
                    'message': 'Отсуствует обязательный параметр "phone"'
                })

            await mongo.opt.find_one_and_update({'phone': phone}, {'$set': {
                'code': ''.join([str(random.randint(0, 9)) for _ in range(6)]),
                'updated_at': datetime.now()
            }}, upsert=True)
            return response.json({
                '_success': True
            })

        elif action == 'check':
            phone = PhoneNumberUtils.normalize(request.json.get('phone'))
            code = StrUtils.to_str(request.json.get('code'))
            if not phone:
                return response.json({
                    '_success': False,
                    'message': 'Отсуствует обязательный параметр "phone"'
                })
            if not code:
                return response.json({
                    '_success': False,
                    'message': 'Отсуствует обязательный параметр "code"'
                })

            otp = await mongo.opt.find_one({'phone': phone})
            if otp and otp['code'] == code and (datetime.now() - otp['updated_at']).total_seconds() <= 60 * 60:
                await mongo.opt.delete_one({'_id': otp['_id']})
                return response.json({
                    '_success': True
                })

            return response.json({
                '_success': False,
                'message': 'Код подтверждения неверный или истёк срок действия'
            })

        elif action == 'viewed':
            ids = ListUtils.to_list_of_strs(request.json.get('ids'))
            ids = ids and [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
            if not ids:
                return response.json({
                    '_success': False,
                    'message': 'Отсуствует обязательный параметр "ids"'
                })

            await mongo.opt.update_many({'_id': {'$in': ids}}, {'$set': {
                'is_active': False
            }})
            return response.json({
                '_success': True
            })

        return response.json({
            '_success': False,
            'message': 'Отсуствует обязательный параметр "action"'
        })
