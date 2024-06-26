FROM python:3.11-slim

# Install ping and curl
RUN apt-get update && \
    apt-get install -y iputils-ping curl

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt --no-cache-dir
ADD . /app
WORKDIR /app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]