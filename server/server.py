import os

from sanic import Sanic
from sanic.exceptions import NotFound

from admin import admin_bp
from admin.api import api_group
from api.core.upload import UploadView
from core.auth import auth
from core.cache import cache
from core.db import mongo, db
from core.session import session
from exceptions import ExceptionsView
from settings import settings

app = Sanic(name='management')

app.config.AUTH_LOGIN_URL = '/admin/login/'
app.config.ACCESS_LOG = False
app.config.RESPONSE_TIMEOUT = 600
app.config.FALLBACK_ERROR_FORMAT = 'html'
app.config.DEBUG = True


@app.listener('before_server_start')
async def initialize_modules(_app, _loop):
    await db.initialize(_loop)
    mongo.initialize(_loop)
    await cache.initialize(_loop, maxsize=5)
    session.initialize(_app)
    auth.initialize(_app)


app.blueprint([
    api_group,
    admin_bp
])

app.add_route(UploadView.as_view(), '/upload/')

app.error_handler.add(NotFound, ExceptionsView.instance().not_found)

app.static('/static', os.path.join(settings.get('file_path'), 'static'))
