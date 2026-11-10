FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY eos ./eos

# Unprivilegierter Benutzer; /data nimmt Datenbank und Netatmo-Token auf.
RUN useradd --system --uid 10001 eos && mkdir /data && chown eos /data
USER eos
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "eos.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
