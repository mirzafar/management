import os

from sanic import Sanic
from sanic_session import Session, AIORedisSessionInterface

from admin import admin
from admin.api import api_group, MainView
from api.core.collection import CollectionView
from api.core.upload import UploadView
from api.ws.chats import chat_messages
from core.auth import auth
from core.cache import cache
from core.db import mongo, db
from settings import settings
from webhooks import webhooks_bp

app = Sanic(name='test')

app.config.AUTH_LOGIN_URL = '/admin/login/'
app.config.ACCESS_LOG = False
app.config.DB_HOST = settings.get('db', {}).get('host', '127.0.0.1')
app.config.DB_DATABASE = settings.get('db', {}).get('database', 'maindb')
app.config.DB_PORT = settings.get('db', {}).get('port', 5432)
app.config.DB_USER = settings.get('db', {}).get('user', 'postgres')
app.config.DB_PASSWORD = settings.get('db', {}).get('password', '1234')
app.config.DB_POOL_MAX_SIZE = 25
app.config.RESPONSE_TIMEOUT = 600
app.config.FALLBACK_ERROR_FORMAT = 'html'
app.config.DEBUG = True

Session(
    app=app,
    interface=AIORedisSessionInterface(
        redis=cache,
        domain=settings['base_url']
    )
)


@app.listener('before_server_start')
async def initialize_modules(_app, _loop):
    mongo.initialize(_loop)
    auth.initialize(_app)
    await cache.initialize(_loop, maxsize=5)
    await db.initialize(_app, _loop)


app.blueprint([
    admin,
    api_group,
    webhooks_bp
])

app.add_route(CollectionView.as_view(), '/collection/<collection_name>/<action>/', name='collection.action')
app.add_route(UploadView.as_view(), '/upload/', name='upload')
app.add_route(MainView.as_view(), '/', name='index')
app.add_websocket_route(chat_messages, '/ws/chats/')

app.static('/static', os.path.join(settings.get('file_path'), 'static'))

if __name__ == '__main__':
    try:
        app.run('127.0.0.1', port=8129, access_log=False)
    except Exception as e:
        print(e)
