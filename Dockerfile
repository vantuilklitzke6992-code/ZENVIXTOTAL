FROM python:3.14-slim

WORKDIR /app
ENV APP_ENV=production

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
