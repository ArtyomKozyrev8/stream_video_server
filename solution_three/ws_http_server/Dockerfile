FROM python:3.9

WORKDIR /usr/src/ws_http_server

COPY ../../requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ../.. .

WORKDIR /usr/src/

CMD python -m aiohttp.web -H 0.0.0.0 -P 7474 ws_http_server:create_app