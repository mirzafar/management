from sanic import Blueprint

from admin.api.cargo.views import ExportTracksView, CustomerTracksView, TracksView

cargo_bp = Blueprint('cargo', url_prefix='/cargo')

cargo_bp.add_route(ExportTracksView.as_view(), '/export/')
cargo_bp.add_route(CustomerTracksView.as_view(), '/customer/')
cargo_bp.add_route(TracksView.as_view(), '/tracks/')
