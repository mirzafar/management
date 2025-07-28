from datetime import datetime

from core.ai import ai_client
from core.db import mongo
from core.handlers import BaseAPIView
from settings import settings
from utils.lists import ListUtils
from utils.strs import StrUtils

system_message = '''Ты — синтез лучших в мире бизнес-аналитиков, системных аналитиков и продакт-менеджеров. Ты обладаешь контекстом по компании, её продуктам и архитектуре на основе предоставленных пользователем данных (загруженных документов и предыдущих фич).

📌 Задача:
На основе описания нового функционала, который ввёл пользователь, тебе нужно:

1. Провести полный анализ функционала.
2. Подготовить два отдельных промта:
   - Один — для генерации BPMN-схем и User Flow через Claude или другой ИИ.
   - Второй — для генерации прототипа дизайна в Figma AI или аналогичных сервисах.

📌 Структура ответа:
---

### 🧩 1. Краткое описание фичи
Сформулируй в 1–2 предложениях, что за функциональность.

### 🎯 2. Цель и ценность фичи
Что она даёт пользователю и бизнесу?

### 🧠 3. Бизнес-анализ:
- Целевая аудитория
- Основная проблема
- Предлагаемое решение
- Ожидаемый результат
- Метрики успеха (KPI)

### 📖 4. Use Case:
Опиши действия ключевых ролей в системе.

### 💬 5. User Stories (формат: Как [роль], я хочу [...], чтобы [...])

### 🔄 6. User Flow (в виде блоков, шагов пользователя)

### 🧭 7. Customer Journey Map (CJM)
В виде таблицы:  
Этап | Действие | Мысли/эмоции | Возможности/точки роста

---

## ✳️ 8. Готовый промт для генерации схем (BPMN + User Flow)
Сформулируй чёткий, структурированный промт, который можно вставить в Claude или другой ИИ-сервис для визуализации схем. Включи все действия, участников и логику бизнес-процесса.

---

## 🎨 9. Готовый промт для генерации UI/UX прототипа
Сформулируй промт для генерации экранов, компонентов, кнопок, логики и визуальных переходов в Figma AI/Uizard/Galileo. Промт должен описывать, какие экраны нужны, что на них должно быть и какую задачу выполняет пользователь на каждом шаге.

---

‼️ Внимание: Используй весь доступный тебе контекст (загруженные документы, архитектуру, прошлые фичи и описание бизнеса клиента). Если контекста недостаточно, задай допущения на основе лучших практик и укажи их явно.'''


class ChatsView(BaseAPIView):
    template_name = 'admin/chats.html'

    async def get(self, request, user):
        query = StrUtils.to_str(request.args.get('query'))

        filters = {
            'is_active': True,
            'user_id': user['id'],
        }

        if query:
            filters['title'] = {'$regex': query, '$options': 'i'}

        items = await mongo.chats.find(filters).sort('_id', -1).to_list(length=None)

        return self.success(request=request, user=user, data={
            'items': items
        })

    async def post(self, request, user):
        prompt = StrUtils.to_str(request.json.get('prompt'))
        file_urls = ListUtils.to_list_of_strs(request.json.get('file_urls'))

        if not prompt:
            return self.error(message='Отсуствует обязательный параметры "Текст"')

        if not file_urls:
            return self.error(message='Отсуствует обязательный параметры "Файл url"')

        content = [
            {'role': 'system', 'content': system_message},
        ]

        for ur in file_urls:
            content.append({
                'type': 'input_file',
                'file_url': f'{settings["base_url"]}/static/uploads/{ur}'
            })

        print("content", content)

        response = await ai_client.responses.create(
            model='gpt-4o',
            input=content,
        )

        if not response.output_text:
            return self.error(message='Операция не выполнена')

        data = {
            'prompt': prompt,
            'file_urls': file_urls,
            'is_active': True,
            'user_id': user['id'],
            'response': response.output_text,
            'created_at': datetime.now()
        }

        inserted = await mongo.chats.insert_one(data)

        if inserted.inserted_id:
            pass
        else:
            return self.error(message='Операция не выполнена')

        return self.success(data={
            'item': data,
            'text': response.output_text
        })
