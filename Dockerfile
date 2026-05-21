FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install tkinter and the minimal X11 client libs needed to draw a window
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-tk \
        tk-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY clock.py .
COPY .env* ./

CMD ["python", "clock.py"]
