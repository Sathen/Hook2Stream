FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOWNLOAD_DIR=/downloads

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && pip install yt-dlp

RUN mkdir -p /downloads

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 3535

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3535"]
