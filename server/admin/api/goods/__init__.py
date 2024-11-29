from sanic import Blueprint

__all__ = ['store_bp']

from admin.api.goods.categories import StoreCategoriesView, StoreCategoryView

store_bp = Blueprint('store', url_prefix='/store')

store_bp.add_route(StoreCategoriesView.as_view(), '/categories/')
store_bp.add_route(StoreCategoryView.as_view(), '/categories/<category_id>/')
