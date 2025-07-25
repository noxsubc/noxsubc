FROM python:3.10.13-slim

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavutil-dev \
        libavfilter-dev \
        libswscale-dev \
        libswresample-dev && \
    rm -rf /var/lib/apt/lists/*

# Copia os arquivos da sua app
WORKDIR /app
COPY . .

# Instala as dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Porta que o Render vai expor
EXPOSE 8000

# Comando para rodar a app (ajuste se for diferente)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
