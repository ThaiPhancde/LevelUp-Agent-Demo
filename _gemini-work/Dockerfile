FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
RUN useradd -u 10001 -m demo && mkdir -p /app/data && chown demo:demo /app/data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest pytest-asyncio
COPY app ./app
COPY tests ./tests
COPY pytest.ini ./pytest.ini
USER demo
EXPOSE 8088
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
