"""Shared test configuration.

Sets baseline environment variables so modules that build Settings work without
a real .env file. No real tokens/credentials are used.
"""

import os

os.environ.setdefault("BOT_TOKEN", "123456:test-token")
os.environ.setdefault("ADMIN_IDS", "111,222")
os.environ.setdefault("CHANNEL_ID", "-1001234567890")
os.environ.setdefault("JOIN_URL", "https://t.me/test_bot?start=join")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/testdb")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
