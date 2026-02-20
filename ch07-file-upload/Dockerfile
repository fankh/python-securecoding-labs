FROM python:3.11-slim

RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV APP_MODE=vulnerable

CMD if [ "$APP_MODE" = "secure" ]; then \
        python secure/app.py; \
    else \
        python vulnerable/app.py; \
    fi
