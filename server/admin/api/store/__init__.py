from sanic import Blueprint

from admin.api.store.categories import StoreCategoriesView, StoreCategoryView
from admin.api.store.expenses import StoreExpensesView, StoreExpenseView
from admin.api.store.goods import StoreGoodsView, StoreGoodView
from admin.api.store.overheads import StoreOverheadsView, StoreOverheadView
from admin.api.store.reasons import StoreReasonsView, StoreReasonView
from admin.api.store.visits import StoreVisitsView, StoreVisitView

__all__ = ['store_bp']

store_bp = Blueprint('store', url_prefix='/store')

store_bp.add_route(StoreCategoriesView.as_view(), '/categories/')
store_bp.add_route(StoreCategoryView.as_view(), '/categories/<category_id>/')

store_bp.add_route(StoreGoodsView.as_view(), '/goods/')
store_bp.add_route(StoreGoodView.as_view(), '/goods/<good_id>/')

store_bp.add_route(StoreOverheadsView.as_view(), '/overheads/')
store_bp.add_route(StoreOverheadView.as_view(), '/overheads/<overhead_id>/')

store_bp.add_route(StoreReasonsView.as_view(), '/reasons/')
store_bp.add_route(StoreReasonView.as_view(), '/reasons/<reason_id>/')

store_bp.add_route(StoreVisitsView.as_view(), '/visits/')
store_bp.add_route(StoreVisitView.as_view(), '/visits/<visit_id>/')

store_bp.add_route(StoreExpensesView.as_view(), '/expenses/')
store_bp.add_route(StoreExpenseView.as_view(), '/expenses/<expense_id>/')
