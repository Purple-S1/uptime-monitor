FROM python:3.12-slim

WORKDIR /app

# Eerst de pakketten installeren (Docker onthoudt deze stap)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Niet als root draaien
RUN useradd --create-home checker
USER checker

CMD ["python", "-u", "checker.py"]
