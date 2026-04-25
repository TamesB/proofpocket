FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# System deps (psycopg binary wheels generally work without build deps; keep image slim)
RUN python -m pip install --no-cache-dir --upgrade pip

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Optional hardening: run as non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Railway/containers typically provide DATABASE_URL, REDIS URLs, etc.
# We run migrate + collectstatic at container start (needs DB connection).
CMD sh -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT}"

