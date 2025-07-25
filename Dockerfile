FROM python:3.13-slim

# Instala dependências de sistema necessárias para ffmpeg/av
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavutil-dev \
        libavfilter-dev \
        libswscale-dev \
        libswresample-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante do código
COPY . /app
WORKDIR /app

# Expõe a porta
EXPOSE 10000

# Comando para iniciar o app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
