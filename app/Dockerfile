FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY stable.py .

EXPOSE 8080

ENV APP_VERSION=1.0
ENV DEPLOYMENT_TIER=Stable

CMD ["python", "stable.py"]
