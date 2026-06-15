#!/bin/sh
set -e

cat > /tmp/servers.json << EOF
{
  "Servers": {
    "1": {
      "Name": "Becas — Local",
      "Group": "Servers",
      "Host": "${POSTGRES_HOST}",
      "Port": ${POSTGRES_PORT},
      "MaintenanceDB": "${POSTGRES_DB}",
      "Username": "${POSTGRES_USER}",
      "SSLMode": "prefer",
      "PassFile": "/tmp/pgpass"
    }
  }
}
EOF

echo "${POSTGRES_HOST}:${POSTGRES_PORT}:*:${POSTGRES_USER}:${POSTGRES_PASSWORD}" > /tmp/pgpass
chmod 600 /tmp/pgpass

exec /entrypoint.sh
