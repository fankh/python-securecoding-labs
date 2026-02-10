FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 기본값: 취약한 버전 실행
ENV APP_MODE=vulnerable

CMD if [ "$APP_MODE" = "secure" ]; then \
        python secure/app.py; \
    else \
        python vulnerable/app.py; \
    fi
