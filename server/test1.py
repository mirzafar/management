from local_settings import settings

print(settings.get('db', {}).get('host'))