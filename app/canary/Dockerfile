FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

ENV APP_VERSION=2.0
ENV DEPLOYMENT_TIER=Canary

CMD ["python", "app.py"]
