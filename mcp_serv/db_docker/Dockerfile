FROM mysql:8

ENV MYSQL_ROOT_PASSWORD=password
ENV MYSQL_DATABASE=trend_tracking_sample

COPY 01_trend_sample.sql /docker-entrypoint-initdb.d/
COPY 02_create_user.sql /docker-entrypoint-initdb.d/