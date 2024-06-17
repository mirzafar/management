from jinja2 import Environment, select_autoescape, FileSystemLoader
from sanic import response

from settings import settings

root_dir = settings.get('root_dir')
TEMPLATE_DIR = '/'.join(root_dir.split('/')[:-1])

env = Environment(
    loader=FileSystemLoader(f'{TEMPLATE_DIR}/templates'),
    autoescape=select_autoescape()
)

_exceptions_instance = None


class ExceptionsView:
    @classmethod
    def instance(cls):
        global _exceptions_instance
        if not _exceptions_instance:
            _exceptions_instance = cls()
        return _exceptions_instance

    @classmethod
    def not_found(cls, request, exception):
        return response.HTTPResponse(env.get_template('errors/404.html').render(
            request=request,
            app=request.app,
            url_for=request.app.url_for
        ), content_type='text/html')
