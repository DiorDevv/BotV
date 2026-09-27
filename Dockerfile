FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Tashkent

# tzdata - konteyner vaqti Toshkent bo'yicha bo'lishi uchun (Sheets/xabarlardagi sana)
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Root bo'lmagan foydalanuvchi bilan ishlaymiz
RUN useradd --create-home --uid 1000 bot \
    && mkdir -p logs tmp data \
    && chown -R bot:bot /app
USER bot

CMD ["python", "bot.py"]
