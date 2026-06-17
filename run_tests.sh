#!/bin/bash

PASS=0
FAIL=0
FAILED_FILES=""

run_test() {
  local file=$1
  local output
  output=$(fardrun test --program "$file" 2>&1)
  echo "$output"
  local p=$(echo "$output" | grep -oE "[0-9]+ passed" | grep -oE "^[0-9]+")
  local f=$(echo "$output" | grep -oE "[0-9]+ failed" | grep -oE "^[0-9]+")
  PASS=$((PASS + ${p:-0}))
  FAIL=$((FAIL + ${f:-0}))
  if [ "${f:-0}" -gt 0 ]; then
    FAILED_FILES="$FAILED_FILES $file"
  fi
}

echo "=== ESCS Test Suite ==="
echo ""

run_test tests/test_sc_jurisdictions.fard
run_test tests/test_sc_event.fard
run_test tests/test_sc_oracle.fard
run_test tests/test_sc_policy.fard
run_test tests/test_sc_provenance.fard
run_test tests/test_sc_recall.fard
run_test tests/test_sc_sensor.fard
run_test tests/test_sc_claim.fard

echo ""
echo "========================="
echo "  total  $PASS passed  $FAIL failed"
echo "========================="

if [ "$FAIL" -gt 0 ]; then
  echo "FAILED: $FAILED_FILES"
  exit 1
fi
