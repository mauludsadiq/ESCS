# ESCS — Epistemic Supply Chain Substrate

A deterministic, cryptographically-verifiable substrate for global supply
chain provenance, built entirely in FARD on top of the EOS epistemic kernel.

Every supply chain event — custody transfer, inspection, temperature reading,
customs clearance, certification, recall — becomes a signed, content-addressed,
policy-gated epistemic claim. Claims are witnessed by independent attestors,
challenged when contested, and permanently recorded on the Anka mesh.

Nothing is asserted. Everything is proven.
No central database. No single point of failure. The mesh is the record.
Deploy anywhere with Docker. Connect via standard HTTP.

---

## By the numbers

   5,254 lines of FARD
     387 tests, 0 failures
       8 source files
       9 test files
      12 commits
      42 jurisdictions across 5 verticals
      18 event types
      42 gate policies
       6 oracle types
       1 live end-to-end scenario verified

---

## What ESCS does differently

Existing supply chain systems rely on trusted central operators, permissioned
databases, and proprietary integrations. ESCS has none of these dependencies.

   Existing systems           ESCS
   ──────────────────────     ──────────────────────────────────────
   Central database           Anka mesh — distributed, no SPOF
   Trusted operator           Ed25519 signatures — math, not trust
   Custom integrations        Standard HTTP + Anka discovery
   Asserted provenance        Cryptographic provenance — proven
   Manual dispute resolution  Automatic weighted witness collapse
   Recall by notification     Recall by signed gossip claim
   Single jurisdiction        42 jurisdictions, 5 verticals
   Opaque audit trail         Full epistemic history, queryable

---

## Architecture

   Institution A          Institution B          Institution C
   (Producer)             (Shipper)              (Customs)
        |                      |                      |
   sign event             sign event             sign event
        |                      |                      |
        +---------- EOS Kernel (claim, gate, witness) ----------+
                               |
                   policy gate evaluation
                   (jurisdiction + reputation + age)
                               |
                       Anka mesh publish
                               |
                   witness attestation
                               |
                   permanent audit trail
                               |
                   ESCS provenance reconstruction
                   (full chain, all witnesses, all challenges)

Institutions connect via standard HTTP. Internal systems (SAP, Oracle, legacy
ERP) post JSON events to an ESCS adapter. The adapter signs and publishes.
The institution never runs FARD. Deploy the adapter with Docker.

---

## Verticals and Jurisdictions (42 total)

### Pharmaceutical (8)

   PHARMA.FDA.DSCSA.v1     US Drug Supply Chain Security Act
                           RepMin(20) + AgeMax(86400)

   PHARMA.EMA.FMD.v1       EU Falsified Medicines Directive
                           RepMin(20) + AgeMax(86400)

   PHARMA.COLD.FDA.v1      FDA cold chain (2-8C)
                           RepMin(10) + AgeMax(3600) — 1 hour freshness

   PHARMA.COLD.WHO.v1      WHO cold chain (vaccines, biologics)
                           RepMin(10) + AgeMax(3600)

   PHARMA.PMDA.v1          Japan PMDA        RepMin(20)
   PHARMA.ANVISA.v1        Brazil ANVISA     RepMin(20)
   PHARMA.MHRA.v1          UK MHRA           RepMin(20)
   PHARMA.RECALL.v1        Global pharma recall  RepMin(50)

### Food (7)

   FOOD.FSMA.v1            US Food Safety Modernization Act  RepMin(10) + AgeMax(86400)
   FOOD.EU.v1              EU food safety                    RepMin(10) + AgeMax(86400)
   FOOD.COLD.v1            Food cold chain (0-4C)            RepMin(5)  + AgeMax(3600)
   FOOD.ORGANIC.USDA.v1    USDA organic certification        RepMin(20)
   FOOD.HALAL.v1           Halal certification               RepMin(20)
   FOOD.KOSHER.v1          Kosher certification              RepMin(20)
   FOOD.RECALL.v1          Food recall                       RepMin(50)

### Electronics (5)

   ELEC.REACH.v1           EU REACH compliance (chemicals)      RepMin(20)
   ELEC.ROHS.v1            EU RoHS (hazardous substances)       RepMin(20)
   ELEC.CONFLICT.v1        Conflict minerals (Dodd-Frank 1502)  RepMin(20)
   ELEC.WEEE.v1            EU WEEE directive (e-waste)          RepMin(10)
   ELEC.ORIGIN.v1          Country of origin                    RepMin(10)

### Apparel (4)

   APPAREL.LABOR.v1        Labor compliance (ILO standards)  RepMin(20)
   APPAREL.ORIGIN.v1       Country of origin                 RepMin(10)
   APPAREL.ORGANIC.v1      Organic fiber certification       RepMin(20)
   APPAREL.FAIR.v1         Fair trade certification          RepMin(20)

### Energy (4)

   ENERGY.REC.v1           Renewable energy certificates  RepMin(20)
   ENERGY.CARBON.v1        Carbon credits                 RepMin(20)
   ENERGY.GRID.v1          Grid provenance                RepMin(10)
   ENERGY.ISO50001.v1      ISO 50001 energy management    RepMin(20)

### Cross-vertical (14)

   SUPPLY.CUSTODY.v1       Custody transfer          RepMin(0)   — any participant
   SUPPLY.INSPECTION.v1    Inspection results        RepMin(5)
   SUPPLY.SENSOR.v1        IoT sensor readings       RepMin(1)   + AgeMax(300)
   SUPPLY.RECALL.v1        Cross-vertical recall     RepMin(50)
   SUPPLY.ISO9001.v1       ISO 9001 quality          RepMin(20)
   SUPPLY.ISO28000.v1      ISO 28000 SC security     RepMin(20)
   SUPPLY.CUSTOMS.US.v1    US CBP customs            RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.EU.v1    EU customs                RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.UK.v1    UK HMRC customs           RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.CN.v1    China customs             RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.JP.v1    Japan customs             RepMin(10)  + AgeMax(86400)
   SUPPLY.ORACLE.v1        Oracle attestations       RepMin(0)
   SUPPLY.STATE.v1         State snapshots           RepMin(0)
   SUPPLY.BATCH.v1         Batch lifecycle           RepMin(0)

---

## Event Types (18)

   Batch lifecycle     batch_created, batch_split, batch_merge
   Custody             custody_transfer
   Inspection          inspection_passed, inspection_failed
   Customs             customs_cleared, customs_held
   Cold chain          temperature_log, temperature_breach
   Certification       certification_issued, certification_revoked
   Recall              recall_issued, recall_acknowledged, recall_resolved
   Sensor              sensor_reading
   Location            location_update
   Origin              origin_attested

---

## Gate Policy Model

Every claim is evaluated by the EOS GateVM (RPN stack machine) before acceptance.

   RepMin(n)       ctx.reputation >= n
   AgeMax(secs)    now - claim.timestamp <= secs
   JurAllow([...]) claim.claim_space in allowed list

Policy hierarchy (strictest to most open):

   recall_policy         RepMin(50)              only highest-rep nodes
   certification_policy  RepMin(20)              accredited certifiers
   pharma_fda_dscsa      RepMin(20) + AgeMax(86400)
   customs_*_policy      RepMin(10) + AgeMax(86400)
   cold_chain_policy     RepMin(10) + AgeMax(3600)  1-hour freshness
   inspection_policy     RepMin(5)
   food_cold_policy      RepMin(5)  + AgeMax(3600)
   sensor_policy         RepMin(1)  + AgeMax(300)   stale after 5 min
   custody_policy        RepMin(0)                  any participant

Policy router:  policy_for(claim_space) -> correct GateVM program
Helpers:        min_reputation_for, max_age_for, requires_age_check

---

## Oracle Model

Oracles are accredited entities whose Ed25519 public keys are registered
in a signed oracle set for a specific jurisdiction.

   Oracle types:
     regulatory      FDA, EMA, PMDA, ANVISA, MHRA
     inspection      SGS, Bureau Veritas, Intertek
     customs         CBP, HMRC, EU customs authorities
     sensor          IoT hardware oracles
     certification   ISO bodies, halal boards, organic certifiers
     recall          FDA, EFSA, MHRA recall authorities

   Lifecycle:
     make_oracle -> sign_oracle (root signs) -> verify_oracle
     revoke_oracle -> oracle_active check
     make_oracle_set -> sign_oracle_set -> verify_oracle_set

   Authorization:
     is_authorized(set, pubkey, jurisdiction, type, now) -> bool
     authorization_report -> detailed rejection reason

   Event signing:
     sign_event(event, oracle_private_key) -> signed envelope
     verify_event_signature(signed_event, oracle_pubkey) -> { valid }

---

## IoT Sensor Architecture

Sensor readings at scale (millions/day) are not published individually.
The aggregation pattern solves the IoT scale problem:

   1. Readings accumulate in a local window buffer (configurable duration)
   2. At window close: aggregate stats + Merkle root computed
   3. ONE claim published per window to Anka mesh
   4. Raw readings content-addressed in k1 storage
   5. Any reading provable against Merkle root on demand

Breach detection runs continuously against the live buffer:
   detect_breach(readings, threshold_min, threshold_max, tolerance_secs)
   A breach claim is always individual, always immediate.
   Breach auto-challenges any active cold chain certification.

Thresholds per jurisdiction:
   FDA cold:  2-8C,   5 min tolerance
   WHO cold:  2-8C,   5 min tolerance
   Food cold: 0-4C,  10 min tolerance

Breach severity: critical (>50% above range), major (>20%), minor (<20%)

Merkle proof: reading_proof(reading, all_readings) -> { included, merkle_root }
Any reading can be proven against the published window claim.

---

## Recall Lifecycle

   recall_issued       Signed by RepMin(50) oracle
                       Propagates via Anka gossip to all batch subscribers
                       One gossip topic per batch per holder
                       class_i -> PHARMA.RECALL.v1
                       class_iii -> SUPPLY.RECALL.v1

   recall_acknowledged Each holder publishes within ack_window:
                       class_i: 24 hours
                       class_ii: 72 hours
                       class_iii: 7 days

   recall_resolved     Holder publishes with quantities and evidence refs
                       quantity_destroyed + quantity_returned

   recall_silence      AgeMax exceeded, no acknowledgement detected
                       Signed non-compliance record published to mesh
                       overdue_secs recorded

Tracker:
   make_ack_tracker(recall_id, expected_holders)
   record_ack, record_resolution, compute_silent
   ack_rate, resolution_rate, is_complete, pending_holders
   non_compliant_holders, recall_status

---

## Provenance Reconstruction

Given a batch ID, ESCS reconstructs the complete epistemic history
from the Anka mesh audit trail. No central database required.

   reconstruct(anka_url, batch_id) returns:
   {
     batch_id, chain_length, chain: [...],
     recalls, recall_count, under_recall,
     current_holder, chain_integrity,
     total_witnesses, total_challenges, contested
   }

Each chain entry:
   { event_kind, claim_space, digest_hex, subject,
     timestamp_unix_secs, issuer_node_id, object,
     witnesses, witness_count, challenges, challenge_count, contested }

Targeted queries:
   custody_chain, inspection_history, temperature_history,
   breaches, customs_history, contested_claims, is_under_recall

Analytics (offline):
   chain_summary, events_by_kind, events_in_window,
   has_breach, has_failed_inspection, has_customs_hold, fully_witnessed

---

## Full Pipeline

   bridge.publish_event(anka_client, kernel, event, timestamp, reputation)

   1. event_to_envelope       — sc_claim converts event to eOS claim
   2. policy_for(claim_space) — select correct GateVM program
   3. eval_gate               — evaluate claim against policy
   4. publish_envelope        — publish to Anka mesh if gate passes
   5. submit_structural       — witness the published claim
   6. return result           — { envelope, gate_result, anka_result,
                                  witness_result, published, witnessed,
                                  claim_space, digest_hex }

Typed pipelines:
   publish_batch_created, publish_custody_transfer,
   publish_inspection, publish_customs, publish_certification,
   publish_origin, publish_location, publish_sensor_window,
   publish_breach, publish_recall, publish_recall_ack,
   publish_recall_resolved, publish_silence, publish_batch

---

## Live Scenario: Pharmaceutical Cold Chain + FDA Class I Recall

Verified end-to-end on Anka node (localhost:18080):

   Step 1   batch_created — Chicago producer, 10,000 units insulin
   Step 2   custody_transfer — producer -> cold storage Chicago
   Step 3   sensor window — 5 readings, 3.1-5.1C, in_range, merkle_root
   Step 4   inspection_passed — FDA certified, rep=5 enforced
   Step 5   custody_transfer — cold storage -> DHL shipper
   Step 6   temperature_breach — 11.2C peak, 3 readings, critical severity
   Step 7   customs_cleared — CBP JFK, rep=10 enforced
   Step 8   custody_transfer — DHL -> distributor NYC
   Step 9   certification_issued — WHO cold chain, rep=20
   Step 10  recall_issued — FDA Class I, rep=50 enforced
            reason: contamination linked to temperature breach
   Step 11  recall_acknowledged — distributor NYC, within 24h window
   Step 12  recall_resolved — 10,000 units destroyed with evidence
   Step 13  silence_check — 0 non-compliant holders
   Step 14  provenance analysis — 9 events, 11 witnesses, 1 challenge
            has_breach: true, active_recalls: 0 (resolved)
   Step 15  audit trail queryable for every claim

---

## Test Suite

   tests/test_sc_jurisdictions.fard   35 tests   42 jurisdictions + predicates
   tests/test_sc_event.fard           34 tests   18 event types
   tests/test_sc_oracle.fard          34 tests   oracle lifecycle + auth
   tests/test_sc_policy.fard          57 tests   42 policies, all verticals
   tests/test_sc_provenance.fard      32 tests   chain reconstruction
   tests/test_sc_recall.fard          39 tests   recall lifecycle
   tests/test_sc_sensor.fard          45 tests   IoT aggregation + breach
   tests/test_sc_claim.fard           36 tests   ESCS -> eOS envelopes
   tests/test_sc_bridge.fard          27 tests   pipeline (14 offline + 13 live)
   tests/test_sc_live.fard            48 tests   live pharma scenario
   ─────────────────────────────────────────────────────────────
   total                             387 tests   0 failures

Run all tests (requires Anka node on localhost:18080 for live tests):

   bash run_tests.sh

Offline tests only (no Anka required):
   fardrun test --program tests/test_sc_jurisdictions.fard
   fardrun test --program tests/test_sc_event.fard
   fardrun test --program tests/test_sc_oracle.fard
   fardrun test --program tests/test_sc_policy.fard
   fardrun test --program tests/test_sc_provenance.fard
   fardrun test --program tests/test_sc_recall.fard
   fardrun test --program tests/test_sc_sensor.fard
   fardrun test --program tests/test_sc_claim.fard

---

## Line Counts

   src/supply_chain/policy.fard        482
   src/supply_chain/event.fard         404
   src/supply_chain/provenance.fard    299
   src/supply_chain/oracle.fard        260
   src/supply_chain/bridge.fard        253
   src/supply_chain/sensor.fard        236
   src/supply_chain/claim.fard         218
   src/supply_chain/recall.fard        211
   src/supply_chain/jurisdictions.fard 171
   ──────────────────────────────────────
   source total                      2,534
   test total                        2,720
   grand total                       5,254

---

## Dependencies

   EOS kernel (github.com/mauludsadiq/EOS)
     claim, gate, witness, keypair, kernel, canonical
   Anka mesh (github.com/mauludsadiq/Anka)
     HTTP node, default localhost:18080
   FARD runtime v1.7.0

---

## Stack

   ESCS       supply chain provenance substrate   this repo
   EOS        epistemic kernel                    claims, gates, witnesses
   Anka       coordination mesh                   publish, audit, discover
   Azim       deterministic AI training           receipts as claims
   Fard Dinar deterministic monetary protocol     transactions as claims
   FARD       language + runtime                  deterministic, receipted

---

## Repositories

   github.com/mauludsadiq/ESCS       this repo
   github.com/mauludsadiq/EOS        epistemic kernel (2,948 lines)
   github.com/mauludsadiq/Anka       coordination mesh (14,506 lines)
   github.com/mauludsadiq/Azim       deterministic AI training

---

## License

MUI
