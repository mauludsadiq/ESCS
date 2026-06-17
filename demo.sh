#!/bin/bash
# ESCS demo — pharmaceutical cold chain scenario
# Requires: docker compose up anka gatewayd witnessd telemetryd

set -e

ANKA=${ANKA:-http://localhost:18080}
GATEWAY=${GATEWAY:-http://localhost:7700}

echo "=== ESCS Demo — Pharmaceutical Cold Chain ==="
echo ""

echo "1. Checking Anka mesh health..."
curl -sf $ANKA/health | python3 -m json.tool | grep -E "ok|claim_count|witness_count"
echo ""

echo "2. Checking ESCS gateway health..."
curl -sf $GATEWAY/health | python3 -m json.tool
echo ""

echo "3. Evaluating FDA cold chain policy..."
curl -sf -X POST $GATEWAY/eval \
  -H "Content-Type: application/json" \
  -d '{
    "claim": {
      "claim_space": "PHARMA.COLD.FDA.v1",
      "subject": "sc:temperature_log:batch:DEMO-001",
      "predicate": "temperature_log",
      "object": "{}",
      "evidence_refs": [],
      "issuer_node_id": "ed25519:demo",
      "timestamp_unix_secs": '"$(date +%s)"'
    },
    "ctx": {
      "reputation": 10,
      "now": '"$(date +%s)"'
    }
  }' | python3 -m json.tool
echo ""

echo "4. Compiling FDA DSCSA policy..."
curl -sf -X POST $GATEWAY/compile \
  -H "Content-Type: application/json" \
  -d '{
    "policy": "{\"rules\":[{\"op\":\"JurAllow\",\"list\":[\"PHARMA.FDA.DSCSA.v1\"]},{\"op\":\"RepMin\",\"val\":20},{\"op\":\"Glb\",\"n\":2}]}"
  }' | python3 -m json.tool
echo ""

echo "=== Demo complete ==="
