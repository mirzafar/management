from sanic import Blueprint

from .list import LessonsView

__all__ = ['lessons_bp']

lessons_bp = Blueprint('lessons', url_prefix='/lessons')

# Lessons
lessons_bp.add_route(LessonsView.as_view(), '/')
