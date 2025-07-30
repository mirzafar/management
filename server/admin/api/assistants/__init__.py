from sanic import Blueprint

from admin.api.assistants.list import AssistantsView

__all__ = ['assistants_bp']

assistants_bp = Blueprint('assistants', url_prefix='/assistants')

assistants_bp.add_route(AssistantsView.as_view(), '/')
