FROM python:3.11-slim

RUN mkdir /app
ADD requirements.txt /app
ADD server.py /app

WORKDIR /app
RUN pip install -r requirements.txt

ENTRYPOINT python3 -m uvicorn --host 0.0.0.0 server:fastapi_app --port 8000
EXPOSE 8000
