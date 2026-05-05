# Dockerfile for Liverpool Automatic
FROM python:3.11-slim

# Evitar prompts de apt
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema y Edge
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    curl \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libvulkan1 \
    --no-install-recommends && \
    # Instalar Microsoft Edge
    curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && \
    install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/ && \
    echo "deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list && \
    rm microsoft.gpg && \
    apt-get update && \
    apt-get install -y microsoft-edge-stable && \
    # Limpiar
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto de la web
EXPOSE 8000

# Variables de entorno por defecto
ENV DOCKER_MODE=true
ENV WEB_USER=emmanuel
ENV WEB_PASS=4mmA180516
ENV BASE_DIR=/data/auto
ENV EDGE_DATA_DIR=/data/edge_profile

# Crear directorios de datos
RUN mkdir -p /data/auto /data/edge_profile

# Comando para iniciar la app
CMD ["python", "web_app.py"]
