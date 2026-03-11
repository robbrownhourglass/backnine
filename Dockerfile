FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 5080

CMD ["gunicorn", "--bind", "0.0.0.0:5080", "--workers", "2", "--threads", "4", "--timeout", "120", "app:app"]
