FROM python:3.11-slim

# Niech logi lecą od razu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Systemowe minimalne zależności (certy, curl do healthchecków itd.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


# Najpierw requirements (cache warstw)
COPY requirements*.txt /app/

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

# Potem reszta kodu
COPY . /app

# Skrypt startowy
COPY entrypoint.sh /entrypoint.sh
ENV PYTHONPATH=/app
RUN chmod +x /entrypoint.sh

# Streamlit domyślnie słucha na 8501
EXPOSE 8501

ENTRYPOINT ["/entrypoint.sh"]
