#!/bin/sh
# ESCS node entrypoint

ANKA_URL=${ANKA_URL:-http://localhost:18080}
GATEWAYD_PORT=${GATEWAYD_PORT:-7700}
WITNESSD_PORT=${WITNESSD_PORT:-7701}
TELEMETRYD_PORT=${TELEMETRYD_PORT:-7702}
NODE_SEED=${NODE_SEED:-escs-default-node}

echo "[escs] starting with ANKA_URL=$ANKA_URL"
echo "[escs] gatewayd=$GATEWAYD_PORT witnessd=$WITNESSD_PORT telemetryd=$TELEMETRYD_PORT"

exec "$@"
