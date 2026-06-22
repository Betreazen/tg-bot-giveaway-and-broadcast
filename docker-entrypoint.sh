#!/bin/sh
# Apply database migrations, then start the bot.
# `alembic upgrade head` is safe to run on every start: it only applies pending
# migrations and is a no-op once the DB is up to date.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting bot..."
exec python -m bot.main
