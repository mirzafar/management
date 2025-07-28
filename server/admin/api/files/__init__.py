from sanic import Blueprint

from admin.api.files.item import FileView
from admin.api.files.list import FilesView

__all__ = ['files_bp']

files_bp = Blueprint('files', url_prefix='/files')

files_bp.add_route(FilesView.as_view(), '/')
files_bp.add_route(FileView.as_view(), '/<file_id>/')
