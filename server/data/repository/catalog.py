import traceback

import httpx

from data.repository.goods import ControlGoodsRepository
from settings import settings

CATALOG_TITLE = (f'1) Хлеб из зеленой гречки без мед\n'
                 f'2) Хлеб из зеленой гречки с мед (кунжут или семечки можно в комментарии)\n'
                 f'3) Хлеб из пророшенной пшеницы без мед\n'
                 f'4) Хлеб Бионан из пророщенной пшеницы с мед (кунжут или семечки можно в комментарии)')


async def on_catalog(chat_id: str) -> dict:
    goods = await ControlGoodsRepository.get_goods()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                url=f'{settings["tg_api_url"]}/bot{settings["tg_token"]}/sendMediaGroup',
                json={
                    'media': [
                        {
                            'type': 'photo',
                            'media': f'{settings["base_url"]}/static/uploads/{img}'
                        } for img in goods.values() if img.get('photo')
                    ],
                    'chat_id': chat_id
                }
            )
    except (Exception,):
        traceback.print_exc()

    text = ''
    counter = 1
    for c in goods.values():
        text += f'{counter}) {c["title"]}\n'
        counter += 1

    return {
        'method': 'sendMessage',
        'text': text,
        'chat_id': chat_id,
        'reply_markup': {
            'keyboard': [
                ['\u2063📔Каталог'],
                ['\u2062📦Заказать'],
                ['\u2062🗃Мои заказы'],
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True,
            'selective': True
        }
    }
