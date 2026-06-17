# ESCS Python SDK

Thin wrapper around the ESCS adapter HTTP API.

## Install

    pip install requests

## Quickstart

    from escs import ESCSClient

    client = ESCSClient("http://localhost:7710")

    receipt = client.custody_transfer(
        batch_id="batch:LOT-001",
        from_party="party:producer",
        to_party="party:shipper",
        location="Chicago, IL",
        quantity=1000,
        unit="units",
    )

    print(receipt.ok)           # True
    print(receipt.digest)       # sha256:...
    print(receipt.receipt_url)  # http://localhost:18080/audit/trail/sha256:...
    print(receipt.witnessed)    # True

## All methods

### Batch lifecycle
    client.batch_created(batch_id, product_code, quantity, unit,
                         origin_location, producer_id, lot_number,
                         manufacture_date, expiry_date)

### Custody
    client.custody_transfer(batch_id, from_party, to_party,
                            location, quantity, unit,
                            handoff_method="standard", actor_id="")

### Inspection
    client.inspection_passed(batch_id, inspector_id, inspection_type,
                             location, standards=[], notes="", reputation=5)
    client.inspection_failed(batch_id, inspector_id, inspection_type,
                             location, failure_codes=[], evidence_refs=[])

### Customs
    client.customs_cleared(batch_id, customs_authority, clearance_ref,
                           port_of_entry, destination_country, reputation=10)
    client.customs_held(batch_id, customs_authority, hold_ref,
                        port_of_entry, reason, evidence_refs=[])

### Cold chain
    client.temperature_log(batch_id, sensor_id, location,
                           temp_min_c, temp_max_c, temp_avg_c,
                           window_start, window_end, reading_count)
    client.temperature_breach(batch_id, sensor_id, location,
                              temp_c, threshold_min_c, threshold_max_c,
                              breach_timestamp, duration_secs)

### Certification
    client.certification_issued(batch_id, cert_type, certifier_id,
                                cert_ref, valid_from, valid_until,
                                scope="", reputation=20)
    client.certification_revoked(batch_id, cert_type, certifier_id,
                                 cert_ref, reason, evidence_refs=[])

### Recall
    client.recall_issued(recall_id, affected_batch_ids, affected_lot_numbers,
                         product_code, severity, reason, issuer_id,
                         instructions, regulatory_ref, reputation=50)
    client.recall_acknowledged(recall_id, batch_id, holder_id,
                               quantity_held, location, action_plan)
    client.recall_resolved(recall_id, batch_id, holder_id,
                           resolution, quantity_destroyed, quantity_returned,
                           evidence_refs=[])

### Sensor, Location, Origin
    client.sensor_reading(batch_id, sensor_id, sensor_type, location,
                          value, unit, threshold_min, threshold_max, in_range=True)
    client.location_update(batch_id, actor_id, location,
                           coordinates=None, facility_id="", scan_method="rfid")
    client.origin_attested(batch_id, certifier_id, country_of_origin,
                           region="", facility_id="", standards=[], evidence_refs=[])

### Provenance queries
    prov = client.provenance("batch:LOT-001")
    prov.current_holder      # "party:distributor"
    prov.under_recall        # False
    prov.chain_length        # 5

    client.provenance_summary("batch:LOT-001")
    client.recalls("batch:LOT-001")
    client.custody_chain("batch:LOT-001")
    client.breaches("batch:LOT-001")

### Discovery
    client.health()
    client.jurisdictions()   # all 42 claim spaces
    client.event_types()     # all 18 event types

## Receipt fields

    receipt.ok                   # bool
    receipt.published            # bool
    receipt.witnessed            # bool
    receipt.event_type           # str
    receipt.batch_id             # str
    receipt.claim_space          # e.g. "SUPPLY.CUSTODY.v1"
    receipt.digest               # "sha256:..."
    receipt.issuer_node_id       # "ed25519:..."
    receipt.timestamp_unix_secs  # int
    receipt.receipt_url          # full audit trail URL
    receipt.error                # str or None (on failure)

## Requires

    ESCS adapter: docker compose up anka gatewayd witnessd adapterd
    Or locally:   fardrun run --program src/services/adapterd.fard --out out/adapter
