from jinja2 import Environment, select_autoescape, FileSystemLoader
from sanic import response
from sanic.request import Request
from sanic.views import HTTPMethodView

from core.auth import auth
from core.encoder import encoder
from settings import settings
from utils.dicts import DictUtils
from utils.strs import StrUtils

root_dir = settings.get('root_dir')
TEMPLATE_DIR = '/'.join(root_dir.split('/')[:-1])

env = Environment(
    loader=FileSystemLoader(f'{TEMPLATE_DIR}/templates'),
    autoescape=select_autoescape()
)


class TemplateHTTPView(HTTPMethodView):
    template_name: str = None

    def html(
        self,
        request: Request,
        user: dict,
        data=None
    ):
        data = DictUtils.as_dict(data) or {}
        data.update({
            'base_url': settings['base_url'],
            '_user': user,
        })

        template = env.get_template(self.template_name)
        rendered = template.render(
            request=request,
            app=request.app,
            url_for=request.app.url_for,
            **(data or {})
        )
        return response.HTTPResponse(rendered, content_type='text/html')

    def success(
        self,
        data=None,
        return_type: str = 'json',
    ):
        if return_type == 'json':
            return response.json({'_success': True, **(DictUtils.as_dict(data) or {})}, dumps=encoder.encode)

        elif return_type == 'text':
            return response.text(StrUtils.to_str(data) or '')

        else:
            return response.empty()

    def error(
        self,
        message=None,
        return_type: str = 'json',
    ):
        if return_type == 'json':
            return response.json({'_success': False, 'message': StrUtils.to_str(message)}, dumps=encoder.encode)

        elif return_type == 'text':
            return response.text(StrUtils.to_str(message) or '')

        else:
            return response.empty()


class BaseAPIView(TemplateHTTPView):
    decorators = [auth.login_required()]
