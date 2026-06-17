"""
ESCS Python SDK — Quickstart Example
Pharmaceutical cold chain: batch creation through custody transfer.

Run with:
    pip install requests
    python example.py
"""

from escs import ESCSClient

client = ESCSClient("http://localhost:7710")

# Check health
health = client.health()
print(f"Connected: node={health['node_id'][:20]}...")

# 1. Create batch
r = client.batch_created(
    batch_id="batch:SDK-DEMO-001",
    product_code="DRUG-INSULIN-001",
    quantity=10000,
    unit="units",
    origin_location="Chicago Pharma Facility, IL",
    producer_id="party:producer-chicago",
    lot_number="LOT-SDK-001",
    manufacture_date=1710000000,
    expiry_date=1741536000,
)
print(f"\n1. Batch created: {r}")
print(f"   Receipt: {r.receipt_url}")

# 2. Custody transfer
r = client.custody_transfer(
    batch_id="batch:SDK-DEMO-001",
    from_party="party:producer-chicago",
    to_party="party:cold-storage",
    location="Chicago, IL",
    quantity=10000,
    unit="units",
    handoff_method="refrigerated_truck",
)
print(f"\n2. Custody transfer: {r}")

# 3. Temperature log
r = client.temperature_log(
    batch_id="batch:SDK-DEMO-001",
    sensor_id="sensor:cold-007",
    location="Chicago Cold Storage",
    temp_min_c=2.1,
    temp_max_c=7.8,
    temp_avg_c=4.5,
    window_start=int(__import__("time").time()) - 300,
    window_end=int(__import__("time").time()),
    reading_count=360,
    reputation=10,
)
print(f"\n3. Temperature log: {r}")

# 4. Inspection
r = client.inspection_passed(
    batch_id="batch:SDK-DEMO-001",
    inspector_id="inspector:fda-001",
    inspection_type="fda_gmp",
    location="Chicago Cold Storage",
    standards=["FDA-21CFR-211"],
    notes="all units verified",
    reputation=5,
)
print(f"\n4. Inspection: {r}")

# 5. Customs
r = client.customs_cleared(
    batch_id="batch:SDK-DEMO-001",
    customs_authority="CBP",
    clearance_ref="CBP-2025-001",
    port_of_entry="JFK",
    destination_country="US",
    reputation=10,
)
print(f"\n5. Customs: {r}")

print(f"\nAll receipts on Anka mesh at: http://localhost:18080")
