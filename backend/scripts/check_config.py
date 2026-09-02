from app.core.config import Settings

settings = Settings()

print(settings.database_url)
print(settings.redis_url)