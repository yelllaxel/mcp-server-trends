#!/bin/bash
set -e

DATADIR=/var/lib/mysql

if [ ! -d "$DATADIR/mysql" ]; then
  echo "First boot: initializing MySQL and loading sample data..."
  mariadb-install-db --user=mysql --datadir=$DATADIR > /dev/null

  mysqld_safe --datadir=$DATADIR &
  until mysqladmin ping -h localhost --silent; do sleep 1; done

  mysql -u root <<-EOSQL
    ALTER USER 'root'@'localhost' IDENTIFIED BY 'password';
    CREATE DATABASE IF NOT EXISTS trend_tracking_sample;
EOSQL
  mysql -u root -ppassword trend_tracking_sample < /docker-entrypoint-initdb.d/01_trend_sample.sql
  mysql -u root -ppassword < /docker-entrypoint-initdb.d/02_create_user.sql
  mysqladmin -u root -ppassword shutdown
fi

mysqld_safe --datadir=$DATADIR &
until mysqladmin ping -h localhost --silent; do sleep 1; done

echo "MySQL ready. Starting MCP server..."
exec python server.py