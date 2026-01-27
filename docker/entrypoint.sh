#!/bin/sh
set -e
mkdir -p static media logs staticfiles

echo "Waiting for database..."
while ! python -c "
import os, socket
h = os.environ.get('DB_HOST', 'db')
p = int(os.environ.get('DB_PORT', '5432'))
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.settimeout(2)
    s.connect((h, p))
    s.close()
except Exception:
    exit(1)
" 2>/dev/null; do sleep 2; done
echo "Database ready."

python manage.py migrate --noinput

if [ -n "$LOAD_DEV_DATA" ] && [ "$LOAD_DEV_DATA" != "0" ]; then
  echo "Loading dev data (categories + sample)..."
  python manage.py load_dev_data
fi

exec "$@"
