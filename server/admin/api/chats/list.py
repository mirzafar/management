import asyncio
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
    @classmethod
    async def create_assistant(cls):
        assistant = await ai_client.beta.assistants.create(
            name='Бизнес-Аналитик',
            instructions=system_message,
            model='gpt-4o',
            tools=[{'type': 'code_interpreter'}, {'type': 'file_search'}]
        )
        return assistant

    @classmethod
    async def function(cls, chat_id, prompt, mode, upload_file_ids, file_urls):
        if mode in ['upload_file', 'url']:
            content = [
                {'role': 'system', 'content': system_message},
            ]

            if mode == 'upload_file':
                for file_id in upload_file_ids:
                    content.append({
                        'role': 'user',
                        'content': [{
                            'type': 'input_file',
                            'file_id': file_id
                        }]
                    })
            else:
                for f_url in file_urls:
                    content.append({
                        'role': 'user',
                        'content': [{
                            'type': 'input_file',
                            'file_url': f'{settings["base_url"]}/static/uploads/{f_url}'
                        }]
                    })

            content.append({
                'role': 'user',
                'content': [
                    {'type': 'input_text', 'text': prompt}
                ]
            })

            print(f'ChatsView#post() -> mode: {mode}, content: {content}')

            response = await ai_client.responses.create(
                model='gpt-4o',
                input=content
            )

            print(f'ChatsView#post() -> mode: {mode}, done, output_text: {response.output_text}')
            if response.output_text:
                response_txt = response.output_text
            else:
                return

        else:
            assistant = await cls.create_assistant()
            print(f'ChatsView#post() -> mode: {mode}, assistant: {assistant.id}')
            thread = await ai_client.beta.threads.create(
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                        'attachments': [
                            {
                                'file_id': file_id,
                                'tools': [{'type': 'code_interpreter'}]
                            } for file_id in upload_file_ids
                        ]
                    }
                ]
            )

            print(f'ChatsView#post() -> mode: {mode}, thread: {thread.id}')
            run = await ai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )

            while True:
                run_status = await ai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run_status.status == 'completed':
                    break
                elif run_status.status in ['failed', 'cancelled', 'expired']:
                    return
                await asyncio.sleep(1)

            print(f'ChatsView#post() -> mode: {mode}, done')
            messages = await ai_client.beta.threads.messages.list(thread_id=thread.id)
            response_txt = messages.data[0].content[0].text.value

        await mongo.chats.update_one({'_id': chat_id}, {'$set': {
            'response': response_txt,
            'is_finished': True
        }})

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
        upload_file_ids = ListUtils.to_list_of_strs(request.json.get('upload_file_ids'))
        mode = StrUtils.to_str(request.json.get('mode'))

        print(f'ChatsView#post() -> mode: {mode}')

        if not prompt:
            return self.error(message='Отсуствует обязательный параметры "Текст"')

        if not file_urls:
            return self.error(message='Отсуствует обязательный параметры "Файл url"')

        if not upload_file_ids:
            return self.error(message='Отсуствует обязательный параметры "upload_file_ids"')

        if not mode:
            return self.error(message='Отсуствует обязательный параметры "Режим"')

        data = {
            'prompt': prompt,
            'file_urls': file_urls,
            'mode': mode,
            'is_active': True,
            'user_id': user['id'],
            'is_finished': False,
            'response': None,
            'created_at': datetime.now()
        }

        inserted = await mongo.chats.insert_one(data)
        if not inserted.inserted_id:
            return self.error(message='Операция не выполнена')

        asyncio.create_task(self.function(
            chat_id=inserted.inserted_id,
            prompt=prompt,
            mode=mode,
            upload_file_ids=upload_file_ids,
            file_urls=file_urls
        ))

        return self.success(data={
            'item': {
                '_id': inserted.inserted_id
            }
        })
