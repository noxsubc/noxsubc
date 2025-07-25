# Usa Python 3.10.13
FROM python:3.10.13-slim

# Instala as dependências de sistema necessárias pro 'av'
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

# Cria diretório de trabalho
WORKDIR /app

# Copia arquivos do projeto
COPY . .

# Atualiza pip e instala dependências
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe a porta que seu app usa
EXPOSE 8000

# Comando para rodar o servidor (ajuste conforme sua app)
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
