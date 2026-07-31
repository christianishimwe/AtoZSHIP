FROM python:3.13

WORKDIR /app

RUN pip install --no-cache-dir Faker

COPY main.py .

COPY other.py .



CMD [ "python", "/app/main.py" ]