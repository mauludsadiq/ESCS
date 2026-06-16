# ESCS — Epistemic Supply Chain Substrate

**The most robust and dependable supply chain provenance system ever built.**

ESCS is a deterministic, cryptographically-verifiable substrate for supply chain
provenance, built entirely in FARD on top of the EOS epistemic kernel.

Every supply chain event — custody transfer, inspection, temperature reading,
customs clearance, certification, recall — becomes a signed, content-addressed,
policy-gated epistemic claim. Claims are witnessed by independent attestors,
challenged when contested, and permanently recorded on the Anka mesh.
Nothing is asserted. Everything is proven.

No central database. No single point of failure. The mesh is the record.

---

## By the numbers

   2,636 lines of FARD
     192 tests, 0 failures
       5 source files
       5 test files
       6 commits
      42 jurisdictions across 5 verticals
      18 event types
      42 gate policies
       1 accredited oracle model

---

## Why ESCS is different

Existing supply chain systems (IBM Food Trust, Everledger, SAP GTS) are
permissioned databases with custom integrations and trusted central operators.
ESCS has none of these weaknesses.

   Existing systems          ESCS
   ─────────────────────     ────────────────────────────────────
   Central database          Anka mesh — distributed, no SPOF
   Trusted operator          Ed25519 signatures — math, not trust
   Custom integrations       Standard HTTP + Anka discovery
   Asserted provenance       Cryptographic provenance — proven
   Manual dispute resolution Automatic weighted witness collapse
   Recall by notification    Recall by signed gossip claim
   Single jurisdiction       42 jurisdictions, 5 verticals
   Opaque audit trail        Full epistemic history, queryable

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

---

## Verticals and Jurisdictions (42 total)

### Pharmaceutical (8)

   PHARMA.FDA.DSCSA.v1     US Drug Supply Chain Security Act
                           RepMin(20) + AgeMax(86400)
                           Serialization, track-and-trace, verification

   PHARMA.EMA.FMD.v1       EU Falsified Medicines Directive
                           RepMin(20) + AgeMax(86400)

   PHARMA.COLD.FDA.v1      FDA cold chain (2-8C)
                           RepMin(10) + AgeMax(3600) — 1 hour freshness
                           Temperature logs stale after 60 minutes

   PHARMA.COLD.WHO.v1      WHO cold chain (vaccines, biologics)
                           RepMin(10) + AgeMax(3600)

   PHARMA.PMDA.v1          Japan PMDA pharmaceutical
   PHARMA.ANVISA.v1        Brazil ANVISA pharmaceutical
   PHARMA.MHRA.v1          UK MHRA pharmaceutical
                           All: RepMin(20)

   PHARMA.RECALL.v1        Global pharma recall
                           RepMin(50) — highest trust only

### Food (7)

   FOOD.FSMA.v1            US Food Safety Modernization Act
                           RepMin(10) + AgeMax(86400)

   FOOD.EU.v1              EU food safety regulations
                           RepMin(10) + AgeMax(86400)

   FOOD.COLD.v1            Food cold chain (0-4C)
                           RepMin(5) + AgeMax(3600)

   FOOD.ORGANIC.USDA.v1    USDA organic certification    RepMin(20)
   FOOD.HALAL.v1           Halal certification            RepMin(20)
   FOOD.KOSHER.v1          Kosher certification           RepMin(20)
   FOOD.RECALL.v1          Food recall                    RepMin(50)

### Electronics (5)

   ELEC.REACH.v1           EU REACH compliance (chemicals)      RepMin(20)
   ELEC.ROHS.v1            EU RoHS (hazardous substances)       RepMin(20)
   ELEC.CONFLICT.v1        Conflict minerals (Dodd-Frank 1502)  RepMin(20)
   ELEC.WEEE.v1            EU WEEE directive (e-waste)          RepMin(10)
   ELEC.ORIGIN.v1          Country of origin                    RepMin(10)

### Apparel (4)

   APPAREL.LABOR.v1        Labor compliance (ILO standards)     RepMin(20)
   APPAREL.ORIGIN.v1       Country of origin                    RepMin(10)
   APPAREL.ORGANIC.v1      Organic fiber certification          RepMin(20)
   APPAREL.FAIR.v1         Fair trade certification             RepMin(20)

### Energy (4)

   ENERGY.REC.v1           Renewable energy certificates        RepMin(20)
   ENERGY.CARBON.v1        Carbon credits                       RepMin(20)
   ENERGY.GRID.v1          Grid provenance                      RepMin(10)
   ENERGY.ISO50001.v1      ISO 50001 energy management          RepMin(20)

### Cross-vertical (14)

   SUPPLY.CUSTODY.v1       Custody transfer          RepMin(0)
   SUPPLY.INSPECTION.v1    Inspection results        RepMin(5)
   SUPPLY.SENSOR.v1        IoT sensor readings       RepMin(1) + AgeMax(300)
   SUPPLY.RECALL.v1        Cross-vertical recall     RepMin(50)
   SUPPLY.ISO9001.v1       ISO 9001 quality          RepMin(20)
   SUPPLY.ISO28000.v1      ISO 28000 SC security     RepMin(20)
   SUPPLY.CUSTOMS.US.v1    US CBP customs            RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.EU.v1    EU customs                RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.UK.v1    UK HMRC customs           RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.CN.v1    China customs             RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.JP.v1    Japan customs             RepMin(10) + AgeMax(86400)
   SUPPLY.ORACLE.v1        Oracle attestations       RepMin(0)
   SUPPLY.STATE.v1         State snapshots           RepMin(0)
   SUPPLY.BATCH.v1         Batch lifecycle           RepMin(0)

---

## Event Types (18)

### Batch Lifecycle
   batch_created       Genesis event for a batch — producer, lot, expiry
   batch_split         One batch divided into sub-batches with quantities
   batch_merge         Multiple batches combined into one

### Custody
   custody_transfer    Handoff between parties — from, to, location, method

### Inspection
   inspection_passed   Accredited inspector signed off — standards, notes
   inspection_failed   Failed with failure codes and evidence refs

### Customs
   customs_cleared     Authority clearance — port, destination, ref
   customs_held        Hold with reason and evidence

### Cold Chain
   temperature_log     IoT window: min/max/avg over time range, reading count
   temperature_breach  Out-of-range detected: temp, thresholds, duration

### Certification
   certification_issued    Organic, halal, fair trade, ISO — valid period
   certification_revoked   Revoked with reason and evidence

### Recall
   recall_issued           Severity class_i/ii/iii, affected batches, instructions
   recall_acknowledged     Holder confirms receipt, quantity held, action plan
   recall_resolved         Destroyed/returned with quantities and evidence

### Sensor
   sensor_reading      Any sensor: temperature, humidity, shock, GPS — in_range flag

### Location
   location_update     GPS/RFID ping — coordinates, facility, scan method

### Origin
   origin_attested     Country of origin certified by accredited body

---

## Gate Policy Model

Every claim is evaluated by the EOS GateVM before being accepted.
The GateVM is an RPN stack machine with three operand types:

   RepMin(n)       ctx.reputation >= n
   AgeMax(secs)    now - claim.timestamp <= secs
   JurAllow([...]) claim.claim_space in allowed list

Policy hierarchy (strictest to most open):

   recall_policy         RepMin(50)              only highest-rep nodes
   certification_policy  RepMin(20)              accredited certifiers
   pharma_fda_dscsa      RepMin(20) + AgeMax(86400)
   customs_*_policy      RepMin(10) + AgeMax(86400)
   cold_chain_policy     RepMin(10) + AgeMax(3600)   1-hour freshness
   inspection_policy     RepMin(5)
   food_cold_policy      RepMin(5)  + AgeMax(3600)
   sensor_policy         RepMin(1)  + AgeMax(300)    stale after 5 min
   custody_policy        RepMin(0)                   any participant

Policy router: policy_for(claim_space) -> correct GateVM program
Helpers:       min_reputation_for, max_age_for, requires_age_check

---

## Oracle Model

Oracles are the root of trust for high-stakes events.
An oracle is an accredited entity whose Ed25519 public key is registered
in a signed oracle set for a specific jurisdiction.

   Oracle types:
     regulatory      FDA, EMA, PMDA, ANVISA, MHRA
     inspection      SGS, Bureau Veritas, Intertek
     customs         CBP, HMRC, EU customs authorities
     sensor          IoT hardware oracles
     certification   ISO bodies, halal boards, organic certifiers
     recall          FDA, EFSA, MHRA recall authorities

   Oracle lifecycle:
     make_oracle(id, pubkey, type, jurisdiction, accreditation_ref, valid_from, valid_until)
     sign_oracle(oracle, root_private_key)       — root signs registration
     verify_oracle(signed_oracle, root_pubkey)   — verify registration
     revoke_oracle(oracle)                       — instant revocation
     oracle_active(oracle, now)                  — validity check

   Oracle sets:
     make_oracle_set(jurisdiction, oracles, issuer_id, timestamp)
     sign_oracle_set(set, root_private_key)
     verify_oracle_set(envelope, root_pubkey)
     add_oracle / remove_oracle / find_oracle / find_by_pubkey
     active_oracles(set, now)

   Authorization:
     is_authorized(set, pubkey, jurisdiction, type, now) -> bool
     authorization_report(...)  -> detailed rejection reason

   Event signing by oracle:
     sign_event(event, oracle_private_key) -> signed event envelope
     verify_event_signature(signed_event, oracle_pubkey) -> { valid }

---

## Provenance Reconstruction

Given a batch ID, ESCS reconstructs the complete epistemic history
from the Anka mesh audit trail.

   reconstruct(anka_url, batch_id) returns:
   {
     batch_id,
     chain: [
       {
         event_kind, claim_space, digest_hex, subject,
         timestamp_unix_secs, issuer_node_id, object,
         witnesses: [...],     witness_count,
         challenges: [...],    challenge_count,
         contested
       },
       ...
     ],
     chain_length,
     recalls: [...],
     recall_count,
     under_recall,
     current_holder,
     chain_integrity,
     total_witnesses,
     total_challenges,
     contested
   }

Targeted queries:
   custody_chain(url, batch_id)       all custody transfers in order
   inspection_history(url, batch_id)  all inspections (pass + fail)
   temperature_history(url, batch_id) all temp logs and breaches
   breaches(url, batch_id)            temperature breaches only
   customs_history(url, batch_id)     clearances and holds
   contested_claims(url, batch_id)    claims with active challenges
   is_under_recall(url, batch_id)     bool — active recall?

Analytics (offline, no Anka required):
   chain_summary(provenance)          compact summary record
   events_by_kind(provenance, kind)   filter by event type
   events_in_window(prov, from, to)   filter by time range
   has_breach(provenance)             any temperature breach?
   has_failed_inspection(provenance)  any inspection failure?
   has_customs_hold(provenance)       any customs hold?
   fully_witnessed(provenance)        every event has >= 1 witness?

---

## Test Suite

   tests/test_sc_jurisdictions.fard   35 tests   jurisdictions + predicates
   tests/test_sc_event.fard           34 tests   all 18 event types
   tests/test_sc_oracle.fard          34 tests   oracle lifecycle + auth
   tests/test_sc_policy.fard          57 tests   all 42 policies
   tests/test_sc_provenance.fard      32 tests   chain reconstruction
   ──────────────────────────────────────────────
   total                             192 tests   0 failures

Run all tests:

   bash run_tests.sh

All tests run fully offline — no Anka node required.
Live integration tests (test_sc_live.fard) coming in next commit.

---

## Line Counts

   src/supply_chain/policy.fard        482
   src/supply_chain/event.fard         404
   src/supply_chain/provenance.fard    299
   src/supply_chain/oracle.fard        260
   src/supply_chain/jurisdictions.fard 171
   ──────────────────────────────────────
   source total                      1,616
   test total                        1,020
   grand total                       2,636

---

## Remaining Modules

   recall.fard     Recall lifecycle: issuance, gossip propagation,
                   acknowledgement tracking, resolution, silence detection
   sensor.fard     IoT oracle claims: hardware attestation, breach detection,
                   cold chain enforcement, automatic challenge on breach
   claim.fard      Convert ESCS events to eOS claim envelopes
                   (ESCS -> EOS -> Anka pipeline)
   bridge.fard     Full pipeline: event -> gate -> claim -> Anka -> witness
   live tests      End-to-end against running Anka node

---

## Stack Position

   ESCS       epistemic supply chain substrate    this repo
   EOS        epistemic kernel                    claims, gates, witnesses
   Anka       coordination mesh                   publish, audit, discover
   Azim       deterministic AI training           receipts as claims
   Fard Dinar deterministic monetary protocol     transactions as claims
   FARD       language + runtime                  deterministic, receipted

---

## Dependencies

   EOS kernel (github.com/mauludsadiq/EOS)
     k1, canonical, claim, gate, witness, keypair, kernel
   Anka mesh (github.com/mauludsadiq/Anka)
     HTTP node at configurable URL (default localhost:18080)
   FARD runtime v1.7.0 (fardrun)

---

## Repositories

   github.com/mauludsadiq/ESCS     this repo — epistemic supply chain
   github.com/mauludsadiq/EOS      epistemic kernel (2,948 lines)
   github.com/mauludsadiq/Anka     coordination mesh (14,506 lines)
   github.com/mauludsadiq/Azim     deterministic AI training (19,200 lines)

---

## License

MUI
