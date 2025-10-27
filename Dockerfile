FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev pkg-config \
    libcairo2 libcairo2-dev libpangocairo-1.0-0 weasyprint build-essential && \
    apt clean && \
    rm -rf /var/cache/apt/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn[standard] gunicorn

COPY . .

# Use uvicorn for async support with multiple workers
CMD ["uvicorn", "hr_project.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
