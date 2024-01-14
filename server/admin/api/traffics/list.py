from core.db import db
from core.handlers import BaseAPIView
from core.pager import Pager
from core.tools import set_counters
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class TrafficsView(BaseAPIView):

    async def get(self, request, user):
        pager = Pager()
        pager.set_page(request.args.get('page', 1))
        pager.set_limit(request.args.get('limit', 10))

        query = StrUtils.to_str(request.args.get('query'))
        status = IntUtils.to_int(request.args.get('status'), default=0)

        cond, cond_vars = ['status = {}'], [status]

        if query:
            cond.append('title ILIKE {}')
            cond_vars.append(f'%{query}%')

        cond, _ = set_counters(' AND '.join(cond))

        traffics = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT t.*,
                ( 
                    CASE WHEN tk.id IS NULL THEN NULL
                    ELSE jsonb_build_object(
                        'id', tk.id,
                        'title', tk.title,
                    )
                    END
                ) AS track
            FROM public.traffics t
            LEFT JOIN public.tracks tk ON t.track_id = tk.id
            WHERE %s
            ORDER BY id DESC
            %s
            ''' % (cond, pager.as_query()),
            *cond_vars
        ))

        total = await db.fetchval(
            '''
            SELECT count(*)
            FROM public.tracks
            WHERE %s
            ''' % cond,
            *cond_vars
        ) or 0

        return self.success(request=request, user=user, data={
            '_success': True,
            'traffics': traffics,
            'total': total,
        })
