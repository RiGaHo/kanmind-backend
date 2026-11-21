FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

WORKDIR /app

COPY requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY manage.py ./
COPY core/ ./core/
COPY accounts_app/ ./accounts_app/
COPY boards_app/ ./boards_app/
COPY tasks_app/ ./tasks_app/

RUN groupadd --system --gid 10001 kanmind \
    && useradd --system --uid 10001 --gid kanmind \
       --home-dir /nonexistent --no-create-home kanmind \
    && mkdir -p /data \
    && chown 10001:10001 /data

USER 10001:10001

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-tmp-dir", "/tmp", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

