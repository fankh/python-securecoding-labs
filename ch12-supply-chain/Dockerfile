FROM python:3.11-slim

WORKDIR /app

# 보안 검사 도구 설치
RUN pip install --no-cache-dir pip-audit safety cyclonedx-bom requests

COPY . .

CMD ["python", "scan_dependencies.py"]
