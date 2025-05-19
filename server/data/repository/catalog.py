from data.repository.goods import ControlGoodsRepository
from local_settings import settings


async def on_catalog(chat_id: str) -> dict:
    goods = await ControlGoodsRepository.get_goods()
    inline_keyboard = []
    for g in goods.values():
        inline_keyboard.append([{'text': g['title'], 'callback_data': f'catalog:select:{g["id"]}'}])

    return {
        'method': 'sendMessage',
        'text': 'Выберите товар',
        'chat_id': chat_id,
        'reply_markup': {
            'inline_keyboard': inline_keyboard
        }
    }


async def on_selected(chat_id: str, _id: str) -> dict:
    goods = await ControlGoodsRepository.get_goods()
    good = goods[_id]

    payload = {
        'parse_mode': 'HTML',
        'chat_id': chat_id,
        'reply_markup': {
            'keyboard': [
                ['\u2063📔Каталог'],
                ['\u2062📦Заказать'],
                ['\u2061🗃Мои заказы'],
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True,
            'selective': True
        }
    }
    if good.get('photo'):
        payload['method'] = 'sendPhoto'
        payload['photo'] = f'{settings["base_url"]}/static/uploads/{good["photo"]}'
        if good.get('description'):
            payload['caption'] = f'<b>{good["title"]}</b>\n\n{good["description"]}'
        else:
            payload['caption'] = f'{good["title"]}'

        if good.get('price'):
            payload['caption'] += f'\n\nЦена: {good["price"]} тг'
    else:
        payload['method'] = 'sendMessage'
        if good.get('description'):
            payload['text'] = f'<b>{good["title"]}</b>\n\n{good["description"]}'
        else:
            payload['text'] = f'{good["title"]}'

        if good.get('price'):
            payload['text'] += f'\n\nЦена: {good["price"]} тг'

    return payload
