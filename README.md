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

   7,621 lines of FARD
     506 FARD tests, 0 failures
      15 Go SDK tests, 0 failures
      21 Java SDK tests, 0 failures
      27 commits
       8 supply chain modules
       4 service modules
       1 interop module (GS1 EPCIS 2.0)
      42 jurisdictions across 5 verticals
      18 event types
      42 gate policies
       6 oracle types
       5 verticals live tested end-to-end
       4 client SDKs (Python, Node.js, Go, Java)
       1 OpenAPI 3.0.3 specification
       1 provenance dashboard

---

## Quickstart

   # Start the stack
   docker compose up anka gatewayd witnessd adapterd

   # Publish a supply chain event
   curl -X POST http://localhost:7710/events \
     -H "Content-Type: application/json" \
     -d '{"event_type":"custody_transfer","batch_id":"batch:LOT-001",
           "from":"party:producer","to":"party:shipper",
           "location":"Chicago, IL","quantity":1000,"unit":"units"}'

   # Response
   {
     "ok": true,
     "published": true,
     "witnessed": true,
     "claim_space": "SUPPLY.CUSTODY.v1",
     "digest": "sha256:...",
     "receipt_url": "http://localhost:18080/audit/trail/sha256:..."
   }

---

## Client SDKs

All four SDKs wrap the adapter HTTP API. Institutions never handle
keypairs, signing, or FARD. They call methods and receive receipts.

### Python

   pip install requests

   from escs import ESCSClient
   client = ESCSClient("http://localhost:7710")
   r = client.custody_transfer(
       batch_id="batch:LOT-001", from_party="party:a",
       to_party="party:b", location="Chicago", quantity=1000, unit="units"
   )
   print(r.digest)       # sha256:...
   print(r.witnessed)    # True
   print(r.receipt_url)  # http://...

### Node.js (Node 18+, no dependencies)

   const { ESCSClient } = require("./escs")
   const client = new ESCSClient("http://localhost:7710")
   const r = await client.custodyTransfer({
       batchId: "batch:LOT-001", from: "party:a", to: "party:b",
       location: "Chicago", quantity: 1000, unit: "units"
   })
   console.log(r.digest, r.witnessed)

### Go

   client := escs.NewClient("http://localhost:7710")
   r, err := client.CustodyTransfer(ctx, escs.CustodyTransferRequest{
       BatchID: "batch:LOT-001", From: "party:a", To: "party:b",
       Location: "Chicago", Quantity: 1000, Unit: "units",
   })
   fmt.Println(r.Digest, r.Witnessed)

### Java (Java 11+, jackson-databind)

   ESCSClient client = new ESCSClient("http://127.0.0.1:7710");
   Receipt r = client.custodyTransfer(
       ESCSClient.CustodyTransferRequest.builder()
           .batchId("batch:LOT-001").from("party:a").to("party:b")
           .location("Chicago").quantity(1000).unit("units")
           .build()
   );
   System.out.println(r.getDigest() + " " + r.isWitnessed());

### OpenAPI

   sdk/openapi/escs.openapi.json — OpenAPI 3.0.3 specification
   Auto-generates clients in any language via openapi-generator:
   openapi-generator generate -i escs.openapi.json -g rust -o sdk/rust

---

## Architecture

   Institution A          Institution B          Institution C
   (Producer)             (Shipper)              (Customs)
        |                      |                      |
   POST /events           POST /events           POST /events
        |                      |                      |
        +------------- adapterd (port 7710) ----------+
                               |
                   keypair management + signing
                   event routing + validation
                   policy gate evaluation
                               |
                       Anka mesh publish
                               |
                   witness attestation (witnessd)
                               |
                   permanent audit trail
                               |
                   Dashboard (port 8080)
                   EPCIS 2.0 export
                   provenance reconstruction

Institutions connect via standard HTTP. Internal systems (SAP, Oracle,
legacy ERP) POST JSON to the adapter. The adapter handles all cryptography.
Deploy with Docker in minutes. No FARD knowledge required.

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
event. Live tested: organic cotton t-shirts from Bangladesh through Chittagong
Port, UK customs Felixstowe, and Amsterdam distribution to EU retailer.

### Energy
Covers Renewable Energy Certificates (RECs), carbon credits under Verra VCS,
grid provenance for cross-border transfers, and ISO 50001 energy management
certification. RECs and carbon credits require RepMin(20); grid provenance
requires RepMin(10). Live tested: Horns Rev 3 offshore wind farm in Denmark,
50,000 MWh, REC + carbon credit issuance, transfer to German consumer via
ACER cross-border interconnector.

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
runs continuously: a breach claim is always individual and always immediate.
Thresholds are jurisdiction-specific (FDA cold: 2-8C, food cold: 0-4C).

---

## Recall Lifecycle

A recall is issued by a RepMin(50) oracle and propagates via Anka gossip to
all batch topic subscribers. Each holder must acknowledge within the severity
window (class_i: 24h, class_ii: 72h, class_iii: 7 days). Holders who fail to
acknowledge receive a signed non-compliance record — silence becomes evidence.
Resolution requires publishing quantity destroyed or returned with evidence.
The complete lifecycle is fully automated and cryptographically verifiable.

---

## GS1 EPCIS 2.0 Bridge

ESCS speaks EPCIS 2.0 — the lingua franca of supply chain traceability.
DSCSA (US pharma), FSMA (US food), and EU DPP all require EPCIS.

   src/interop/epcis.fard — bidirectional ESCS <-> EPCIS 2.0 mapping

ESCS -> EPCIS (all 18 event types):
   batch_created        -> ObjectEvent ADD,     bizStep: commissioning
   custody_transfer     -> TransactionEvent,    bizStep: shipping
                          sourceList + destinationList + quantityList
   inspection_passed    -> ObjectEvent OBSERVE, disposition: active
   inspection_failed    -> ObjectEvent OBSERVE, disposition: non_conformant
   customs_cleared      -> ObjectEvent OBSERVE, bizStep: entering_exiting
   temperature_log      -> ObjectEvent OBSERVE, sensorElementList (gs1:Temperature)
   temperature_breach   -> ObjectEvent OBSERVE, TEMPERATURE_OUT_OF_RANGE exception
   certification_issued -> ObjectEvent OBSERVE, certificationList
   recall_issued        -> ObjectEvent DELETE,  disposition: recalled
   recall_resolved      -> ObjectEvent DELETE,  disposition: destroyed

EPCIS -> ESCS ingest:
   Any EPCIS 2.0 document can be ingested and converted to ESCS events.
   Every ingested event receives a cryptographic receipt on the Anka mesh.

This makes ESCS a cryptographic audit layer underneath existing EPCIS
implementations — not a replacement for SAP, IBM Food Trust, or TraceLink.

---

## Provenance Dashboard

Single-file HTML dashboard. Wall Street design — Times New Roman,
navy blue (#0a2d5e), gold accent border (#c8a84b).

   cd sdk/dashboard && python3 proxy.py
   open http://localhost:8080

Features: status bar (Anka mesh, claim count, witnesses, adapter),
batch query, breach banner, recall banner, summary grid,
color-coded provenance chain timeline, recall history table.

---

## Adapter API (port 7710)

   POST /events                  publish any supply chain event
   GET  /provenance/:batch_id    provenance query URLs
   GET  /jurisdictions           all 42 known claim spaces
   GET  /events/types            all 18 supported event types
   GET  /health                  service health + node identity

Receipt format:
   { ok, published, witnessed, event_type, batch_id, claim_space,
     digest, issuer_node_id, timestamp_unix_secs, receipt_url }

---

## Live Scenarios Verified

Pharmaceutical — FDA cold chain + Class I recall.
Chicago batch, sensor window (3.1-5.1C), FDA inspection, temperature
breach 11.2C, JFK customs, NYC distributor. Class I recall issued,
acknowledged, resolved (10,000 units destroyed). 9 events, 11 witnesses.

Food — FSMA + USDA organic + E. coli recall.
Organic spinach Salinas Valley, USDA organic, food cold chain (0-4C),
FSMA inspection, LA distributor. Class I E. coli recall. 6 events.

Electronics — REACH + RoHS + conflict minerals.
TSMC Taiwan, RMI conflict minerals, EU REACH, RoHS, Singapore distributor,
EU customs Hamburg. 7 events, 3 certifications, fully witnessed.

Apparel — Labor compliance + organic + fair trade.
Organic cotton Dhaka Bangladesh, GOTS, ILO/SA8000/SEDEX labor audit,
Fairtrade International, UK customs Felixstowe, Amsterdam retailer.
9 events, fully witnessed. Certification revocation included.

Energy — Offshore wind + REC + carbon credits.
Horns Rev 3 Denmark, 50,000 MWh, AIR REC, Verra VCS 25,000 tCO2e,
ISO 50001, grid transfer to Germany via ACER interconnector. 9 events.

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
   tests/test_epcis.fard              41 tests   GS1 EPCIS 2.0 bridge
   sdk/go/escs_test.go                15 tests   Go SDK live
   sdk/java/ESCSTest.java             21 tests   Java SDK live
   ─────────────────────────────────────────────────────────────
   total                             542 tests   0 failures

Run FARD tests (requires Anka on localhost:18080):

   bash run_tests.sh

Run Go SDK tests:

   cd sdk/go && go test -v ./...

Run Java SDK tests:

   cd sdk/java
   javac -cp "jackson-databind.jar:jackson-core.jar:jackson-annotations.jar" \
     src/main/java/supply/escs/ESCSClient.java \
     src/main/java/supply/escs/ESCSTest.java -d out
   java -cp "out:jackson-databind.jar:jackson-core.jar:jackson-annotations.jar" \
     supply.escs.ESCSTest

---

## Docker

   docker build -t escs:latest .
   docker run -d -p 7700:7700 escs:latest

   docker compose up anka gatewayd witnessd telemetryd
   docker compose --profile full up   # includes adapter

Services:
   anka         port 18080   Anka mesh node
   gatewayd     port 7700    claim eval + policy compile
   witnessd     port 7701    witness collection + forwarding
   telemetryd   port 7702    signed telemetry claims
   adapter      port 7710    institution HTTP adapter

---

## Source Modules

   src/supply_chain/
     jurisdictions.fard   42 claim spaces, 5 verticals, predicates
     event.fard           18 event types, routing, severity
     oracle.fard          accredited oracle model, root of trust
     policy.fard          42 gate policies, full vertical coverage
     provenance.fard      chain reconstruction, analytics
     recall.fard          recall lifecycle, silence detection
     sensor.fard          IoT aggregation, Merkle proofs, breach detection
     claim.fard           ESCS events -> eOS claim envelopes
     bridge.fard          full pipeline: event -> gate -> Anka -> witness

   src/interop/
     epcis.fard           GS1 EPCIS 2.0 bidirectional bridge

   src/services/
     adapterd.fard        institution HTTP adapter (port 7710)
     gatewayd.fard        claim evaluation gateway (port 7700)
     witnessd.fard        witness collector (port 7701)
     telemetryd.fard      telemetry service (port 7702)

   sdk/
     python/escs.py       Python SDK (all 18 events)
     python/example.py    Python quickstart
     node/escs.js         Node.js SDK (all 18 events)
     node/example.js      Node.js quickstart
     go/escs.go           Go SDK (all 18 events, context-aware)
     go/escs_test.go      Go SDK tests (15 live)
     java/ESCSClient.java Java SDK (builder pattern, Java 11+)
     java/ESCSTest.java   Java SDK tests (21 live)
     java/Example.java    Java quickstart
     openapi/escs.openapi.json  OpenAPI 3.0.3 specification
     dashboard/index.html provenance dashboard
     dashboard/proxy.py   dev proxy server

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
