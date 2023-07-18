FROM python:2.7-alpine

WORKDIR /app

RUN apk update --no-cache
RUN pip install pyst2

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
