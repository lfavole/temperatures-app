#!/usr/bin/env bash
set -euo pipefail

if [ -n "$VERCEL" ]; then
    uv="python3 -m uv"
    case "$DATABASE_URL" in
        postgres*)
            echo "Installing PostgreSQL..."
            $uv add --no-sync psycopg[binary,pool]~=3.2
            ;;
        mysql*)
            echo "Installing MySQL..."
            apt update
            apt install -y python3-dev default-libmysqlclient-dev build-essential pkg-config
            $uv add --no-sync mysqlclient~=2.2
            ;;
    esac
else
    uv="uv"
fi

# Migrate
$uv run manage.py migrate &

# Collect static files
python3 -m uv run manage.py collectstatic --noinput &

# Compile translation messages (if any .po files are present)
dnf install -y gettext
python3 -m uv run manage.py compilemessages --ignore .venv || true

wait

# Remove the created virtual environment
rm -rf .venv || true
