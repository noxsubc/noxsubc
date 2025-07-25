# Usa Python 3.10.13
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
        libswresample-dev \
        gcc && \
    rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia tudo
COPY . .

# Instala dependências do Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe a porta que seu app vai rodar
EXPOSE 8000

# Comando para iniciar (ajuste se necessário)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
