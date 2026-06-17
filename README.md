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
     465 tests, 0 failures
       8 source modules
      12 test files
      18 commits
      42 jurisdictions across 5 verticals
      18 event types
      42 gate policies
       6 oracle types
       5 verticals live tested end-to-end

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
The institution never runs FARD. Deploy with Docker in minutes.

---

## Verticals

### Pharmaceutical
Covers US FDA DSCSA serialization, EU Falsified Medicines Directive, WHO and
FDA cold chain (2-8C with 1-hour freshness enforcement), and national
authorities in Japan (PMDA), Brazil (ANVISA), and the UK (MHRA). Recalls
require RepMin(50) — the highest trust threshold in the system. Cold chain
claims expire after one hour; a temperature breach automatically challenges
any active cold chain certification. Live tested: batch creation through FDA
Class I recall with full recall resolution and silence detection.

### Food
Covers US FSMA produce safety, EU food safety regulations, cold chain for
perishables (0-4C, stricter than pharma), and certification schemes including
USDA Organic, Halal, and Kosher. FSMA and EU food claims require RepMin(10)
with 24-hour freshness. Food recalls follow the same class-based lifecycle as
pharma recalls. Live tested: farm-to-table organic spinach from Salinas Valley
through USDA organic certification, FSMA inspection, and Class I E. coli recall.

### Electronics
Covers EU REACH (chemical substances), RoHS (hazardous materials), conflict
minerals traceability under Dodd-Frank Section 1502, WEEE end-of-life
registration, and country-of-origin attestation. REACH, RoHS, and conflict
minerals require RepMin(20) from accredited certification bodies. Live tested:
full semiconductor supply chain from TSMC Taiwan through Singapore to EU
customs Hamburg, with conflict minerals, REACH, and RoHS certifications.

### Apparel
Covers labor compliance under ILO core conventions and SA8000, country of
origin, GOTS organic fiber certification, and Fairtrade International
certification. Labor compliance and fair trade require RepMin(20); origin
attestation requires RepMin(10). Certification revocation is a first-class
event — a signed record of why a certification was withdrawn. Live tested:
organic cotton t-shirts from Bangladesh through Chittagong Port, UK customs
at Felixstowe, and Amsterdam distribution to EU retailer.

### Energy
Covers Renewable Energy Certificates (RECs), carbon credits under Verra VCS,
grid provenance for cross-border transfers, and ISO 50001 energy management
certification. RECs and carbon credits require RepMin(20) from accredited
registries; grid provenance requires RepMin(10). Energy custody transfers
use grid-native handoff methods (grid_injection, grid_transfer). Live tested:
Horns Rev 3 offshore wind farm in Denmark generating 50,000 MWh, issuing RECs
and carbon credits, transferring to German consumer via ACER cross-border
interconnector with EU customs clearance.

---

## Jurisdictions (42 total)

### Pharmaceutical (8)
   PHARMA.FDA.DSCSA.v1     RepMin(20) + AgeMax(86400)
   PHARMA.EMA.FMD.v1       RepMin(20) + AgeMax(86400)
   PHARMA.COLD.FDA.v1      RepMin(10) + AgeMax(3600)
   PHARMA.COLD.WHO.v1      RepMin(10) + AgeMax(3600)
   PHARMA.PMDA.v1          RepMin(20)
   PHARMA.ANVISA.v1        RepMin(20)
   PHARMA.MHRA.v1          RepMin(20)
   PHARMA.RECALL.v1        RepMin(50)

### Food (7)
   FOOD.FSMA.v1            RepMin(10) + AgeMax(86400)
   FOOD.EU.v1              RepMin(10) + AgeMax(86400)
   FOOD.COLD.v1            RepMin(5)  + AgeMax(3600)
   FOOD.ORGANIC.USDA.v1    RepMin(20)
   FOOD.HALAL.v1           RepMin(20)
   FOOD.KOSHER.v1          RepMin(20)
   FOOD.RECALL.v1          RepMin(50)

### Electronics (5)
   ELEC.REACH.v1           RepMin(20)
   ELEC.ROHS.v1            RepMin(20)
   ELEC.CONFLICT.v1        RepMin(20)
   ELEC.WEEE.v1            RepMin(10)
   ELEC.ORIGIN.v1          RepMin(10)

### Apparel (4)
   APPAREL.LABOR.v1        RepMin(20)
   APPAREL.ORIGIN.v1       RepMin(10)
   APPAREL.ORGANIC.v1      RepMin(20)
   APPAREL.FAIR.v1         RepMin(20)

### Energy (4)
   ENERGY.REC.v1           RepMin(20)
   ENERGY.CARBON.v1        RepMin(20)
   ENERGY.GRID.v1          RepMin(10)
   ENERGY.ISO50001.v1      RepMin(20)

### Cross-vertical (14)
   SUPPLY.CUSTODY.v1       RepMin(0)   — any participant
   SUPPLY.INSPECTION.v1    RepMin(5)
   SUPPLY.SENSOR.v1        RepMin(1)   + AgeMax(300)
   SUPPLY.RECALL.v1        RepMin(50)
   SUPPLY.ISO9001.v1       RepMin(20)
   SUPPLY.ISO28000.v1      RepMin(20)
   SUPPLY.CUSTOMS.US.v1    RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.EU.v1    RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.UK.v1    RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.CN.v1    RepMin(10)  + AgeMax(86400)
   SUPPLY.CUSTOMS.JP.v1    RepMin(10)  + AgeMax(86400)
   SUPPLY.ORACLE.v1        RepMin(0)
   SUPPLY.STATE.v1         RepMin(0)
   SUPPLY.BATCH.v1         RepMin(0)

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

   recall_policy         RepMin(50)
   certification_policy  RepMin(20)
   pharma_fda_dscsa      RepMin(20) + AgeMax(86400)
   customs_*_policy      RepMin(10) + AgeMax(86400)
   cold_chain_policy     RepMin(10) + AgeMax(3600)
   inspection_policy     RepMin(5)
   food_cold_policy      RepMin(5)  + AgeMax(3600)
   sensor_policy         RepMin(1)  + AgeMax(300)
   custody_policy        RepMin(0)

---

## Oracle Model

Oracles are accredited entities whose Ed25519 public keys are registered
in a signed oracle set for a specific jurisdiction. Six oracle types cover
the full range of supply chain attestation: regulatory bodies (FDA, EMA),
inspection organizations (SGS, Bureau Veritas), customs authorities (CBP,
HMRC), IoT hardware oracles, certification bodies (ISO, Fairtrade, Verra),
and recall-issuing authorities. Oracle sets are root-signed, content-addressed,
and verifiable without contacting any central registry.

---

## IoT Sensor Architecture

Sensor readings accumulate in a local window buffer. At window close, one
claim is published per window — not per reading. The claim includes aggregate
stats (min, max, avg) and a Merkle root over all readings, so any individual
reading can be proven against the published claim on demand. Breach detection
runs continuously: a breach claim is always individual and always immediate,
bypassing the window. Thresholds are jurisdiction-specific (FDA cold: 2-8C,
food cold: 0-4C) with configurable tolerance before a breach is declared.

---

## Recall Lifecycle

A recall is issued by a RepMin(50) oracle and propagates via Anka gossip to
all batch topic subscribers. Each holder must acknowledge within the severity
window (class_i: 24h, class_ii: 72h, class_iii: 7 days). Holders who fail to
acknowledge after the deadline receive a signed non-compliance record —
silence itself becomes evidence. Resolution requires publishing quantity
destroyed or returned with supporting evidence references. The complete
lifecycle — issuance, acknowledgement, resolution, and silence detection —
is fully automated and cryptographically verifiable.

---

## Provenance Reconstruction

Given a batch ID, ESCS reconstructs the complete epistemic history from the
Anka mesh audit trail — every event, every witness, every challenge. No
central database is required. The mesh is the record. Targeted queries return
custody chains, inspection histories, temperature histories, breach lists,
customs trails, and contested claims. Analytics run offline: breach detection,
failed inspection flags, customs holds, witness completeness, and time-window
filtering all operate on the reconstructed provenance record.

---

## Full Pipeline

   bridge.publish_event(anka_client, kernel, event, timestamp, reputation)

   1. event_to_envelope    — ESCS event -> signed eOS claim envelope
   2. policy_for           — select GateVM program for claim_space
   3. eval_gate            — evaluate claim against policy
   4. publish_envelope     — publish to Anka mesh if gate passes
   5. submit_structural    — witness the published claim
   6. return result        — { envelope, gate_result, anka_result,
                              witness_result, published, witnessed,
                              claim_space, digest_hex }

---

## Live Scenarios Verified

All five verticals tested end-to-end on a live Anka node:

**Pharmaceutical** — Offshore cold chain + FDA Class I recall.
Batch created in Chicago, sensor window (3.1-5.1C), FDA inspection, temperature
breach at 11.2C, JFK customs, distributor NYC. FDA issues Class I recall linked
to breach. Distributor acknowledges, destroys 10,000 units with evidence.
Silence check: 0 non-compliant. Full provenance: 9 events, 11 witnesses.

**Food** — Farm-to-table organic produce + E. coli recall.
Organic spinach from Salinas Valley, USDA organic certification, food cold
chain (1.2-3.2C within 0-4C threshold), FSMA inspection, LA distributor.
Class I recall for E. coli O157:H7. Full provenance: 6 events, under recall.

**Electronics** — Semiconductor supply chain, 3 EU compliance certifications.
TSMC Taiwan, conflict minerals (RMI RMAP), REACH (no SVHC), RoHS (EU
Directive), Singapore distributor, EU customs Hamburg. Full provenance:
7 events, 3 certifications, fully witnessed, no recall.

**Apparel** — Ethical fashion, 4 certification types.
Organic cotton Dhaka Bangladesh, GOTS organic fiber, labor compliance (ILO,
SA8000, SEDEX), Fairtrade International, sea freight Chittagong, UK customs
Felixstowe, Amsterdam EU retailer. Certification revocation included.
Full provenance: 9 events, fully witnessed.

**Energy** — Offshore wind, renewable energy certificates + carbon credits.
Horns Rev 3 Denmark, 50,000 MWh generation, REC (AIR), carbon credit (Verra
VCS 25,000 tCO2e), ISO 50001, grid injection to Energinet, EU cross-border
transfer to German consumer via ACER interconnector. Full provenance:
9 events, fully witnessed.

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
   tests/test_sc_bridge.fard          27 tests   pipeline (offline + live)
   tests/test_sc_live.fard            48 tests   pharma cold chain scenario
   tests/test_sc_food_live.fard       20 tests   food vertical live
   tests/test_sc_elec_live.fard       22 tests   electronics vertical live
   tests/test_sc_apparel_live.fard    34 tests   apparel vertical live
   tests/test_sc_energy_live.fard     38 tests   energy vertical live
   ─────────────────────────────────────────────────────────────
   total                             465 tests   0 failures

Run all tests (requires Anka on localhost:18080 for live tests):

   bash run_tests.sh

---

## Docker

   docker build -t escs:latest .
   docker run -d -p 7700:7700 escs:latest
   curl http://localhost:7700/health

   docker compose up anka gatewayd witnessd telemetryd

Services:
   anka         port 18080   Anka mesh node
   gatewayd     port 7700    claim eval + policy compile
   witnessd     port 7701    witness collection + forwarding
   telemetryd   port 7702    signed telemetry claims
   adapter      port 7710    institution HTTP adapter (profile: full)

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
   github.com/mauludsadiq/EOS        epistemic kernel (2,948 lines, 143 tests)
   github.com/mauludsadiq/Anka       coordination mesh (14,506 lines)
   github.com/mauludsadiq/Azim       deterministic AI training

---

## License

MUI
