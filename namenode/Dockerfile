FROM python:3.7

COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 2131
ENTRYPOINT python3 master.py