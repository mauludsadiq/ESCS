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

   8,600 lines of FARD
     555 FARD tests, 0 failures
      40 Python offline signing tests
      38 Node.js offline signing tests
      15 Go SDK tests
      21 Java SDK tests
     669 total tests, 0 failures
      31 commits
       8 supply chain modules
       2 interop modules (GS1 EPCIS 2.0, EU DPP)
      42 jurisdictions across 5 verticals
      18 event types
      42 gate policies
       5 verticals live tested end-to-end
       4 client SDKs (Python, Node.js, Go, Java)
       1 OpenAPI 3.0.3 specification
       1 provenance dashboard
       1 offline signing layer (Python + Node.js)
       1 load test + benchmark

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

   pip install requests cryptography

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

### Go

   client := escs.NewClient("http://localhost:7710")
   r, err := client.CustodyTransfer(ctx, escs.CustodyTransferRequest{
       BatchID: "batch:LOT-001", From: "party:a", To: "party:b",
       Location: "Chicago", Quantity: 1000, Unit: "units",
   })

### Java (Java 11+, jackson-databind)

   ESCSClient client = new ESCSClient("http://127.0.0.1:7710");
   Receipt r = client.custodyTransfer(
       ESCSClient.CustodyTransferRequest.builder()
           .batchId("batch:LOT-001").from("party:a").to("party:b")
           .location("Chicago").quantity(1000).unit("units")
           .build()
   );

### OpenAPI

   sdk/openapi/escs.openapi.json — OpenAPI 3.0.3 specification
   openapi-generator generate -i escs.openapi.json -g rust -o sdk/rust

---

## Offline Signing

Institutions can sign claims locally without the adapter running.
The adapter becomes optional infrastructure — not a required dependency.

   from escs_offline import OfflineSigner, OfflineQueue

   # Generate keypair (deterministic from seed)
   signer = OfflineSigner.generate("my-institution-seed")

   # Sign locally — no network required
   envelope = signer.sign_event({
       "event_type": "custody_transfer",
       "batch_id":   "batch:LOT-001",
       "from":       "party:producer",
       "to":         "party:shipper",
       "location":   "Chicago, IL",
       "quantity":   1000,
       "unit":       "units",
   })
   print(envelope.digest)    # sha256:... — signed locally
   print(envelope.signed)    # True
   print(envelope.published) # False — not yet on Anka

   # Queue for later submission
   queue = OfflineQueue("queue.jsonl")
   queue.enqueue(envelope)

   # Submit when online
   from escs import ESCSClient
   client = ESCSClient("http://localhost:7710")
   receipt = client.submit_signed(envelope)
   print(receipt.published)  # True
   print(receipt.witnessed)  # True

Node.js offline signing works identically via sdk/node/escs_offline.js.

Architecture change:

   Before: institution -> adapter -> sign -> gate -> Anka
   After:  institution -> SDK keypair -> sign locally -> queue
                                                           |
                                                  when online:
                                           /submit_signed -> gate -> Anka

---

## Benchmark

Measured on MacBook Pro (Apple Silicon), single-node local Anka mesh.

   Offline signing       9,286 signs/sec   p50=0.106ms   p99=0.114ms
   Adapter throughput    ~0.1 eps           p50=7.9s      p99=8.4s
   Gate overhead         negligible — all event types identical

The offline signing rate (9,286/sec) means institutions can pre-sign
and queue hours of supply chain activity in seconds. The adapter
round-trip latency (~8s) is dominated by witness collection on a
single-node mesh. Multi-node production deployments drop this to
~500ms-2s as witnesses run concurrently across geographically
distributed nodes.

Key finding: gate evaluation adds no measurable overhead. All 42
policies (RepMin, AgeMax, JurAllow) evaluate in <1ms. The bottleneck
is always witness collection, never policy or signing.

Full benchmark: benchmark/BENCHMARK.md
Raw results: benchmark/results.json

---

## Architecture

   Institution A          Institution B          Institution C
   (Producer)             (Shipper)              (Customs)
        |                      |                      |
   POST /events           POST /events           POST /events
   (or submit_signed)     (or submit_signed)     (or submit_signed)
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
                   EU DPP assembly

---

## Verticals

### Pharmaceutical
Covers US FDA DSCSA serialization, EU Falsified Medicines Directive, WHO and
FDA cold chain (2-8C with 1-hour freshness enforcement), and national
authorities in Japan (PMDA), Brazil (ANVISA), and the UK (MHRA). Recalls
require RepMin(50). Cold chain claims expire after one hour. Live tested:
batch creation through FDA Class I recall, 9 events, 11 witnesses.

### Food
Covers US FSMA produce safety, EU food safety regulations, cold chain for
perishables (0-4C), and certification schemes including USDA Organic, Halal,
and Kosher. Live tested: organic spinach from Salinas Valley through USDA
organic certification, FSMA inspection, and Class I E. coli recall.

### Electronics
Covers EU REACH, RoHS, conflict minerals (Dodd-Frank 1502), WEEE, and
country-of-origin attestation. Live tested: TSMC Taiwan through Singapore
to EU customs Hamburg, with conflict minerals, REACH, and RoHS certifications.

### Apparel
Covers labor compliance (ILO, SA8000), country of origin, GOTS organic fiber,
and Fairtrade International. Live tested: organic cotton from Bangladesh
through UK customs Felixstowe to Amsterdam retailer, 9 events, fully witnessed.

### Energy
Covers RECs, carbon credits (Verra VCS), grid provenance, and ISO 50001.
Live tested: Horns Rev 3 Denmark, 50,000 MWh, REC + carbon credit issuance,
transfer to Germany via ACER cross-border interconnector.

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

Every claim is evaluated by the EOS GateVM before acceptance.

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
   sensor_policy         RepMin(1)  + AgeMax(300)
   custody_policy        RepMin(0)

---

## GS1 EPCIS 2.0 Bridge

ESCS speaks EPCIS 2.0 — the lingua franca of supply chain traceability.
DSCSA (US pharma), FSMA (US food), and EU DPP all require EPCIS.

   src/interop/epcis.fard — bidirectional ESCS <-> EPCIS 2.0 mapping

All 18 ESCS event types map to EPCIS 2.0 events with correct bizStep,
disposition, sourceList, sensorElementList, and certificationList.
Any EPCIS 2.0 document can be ingested and converted to ESCS events.

ESCS sits underneath existing EPCIS implementations — not a replacement
for SAP, IBM Food Trust, or TraceLink. Every EPCIS event gets a
cryptographic receipt on the Anka mesh.

---

## EU Digital Product Passport

ESCS implements the EU ESPR Digital Product Passport schema, assembled
from provenance events on the Anka mesh.

   src/interop/dpp.fard          — DPP schema + assembly
   src/interop/dpp_verticals.fard — vertical profiles

Mandate timeline:
   2027: Apparel, Energy/Batteries
   2028: Electronics, ICT equipment
   2029: Pharma, Food, Construction
   2030: Other categories

DPP structure (EU ESPR compliant):
   identity          product_code, lot_number, model, serial, dates
   manufacturer      producer_id, name, country, facility
   materials         substance list, recycled_content_pct, REACH flag
   carbon_footprint  total/scope1/scope2/scope3 kgCO2e, methodology
   compliance        declarations list, CE marking, RoHS, REACH, WEEE
   supply_chain      ESCS provenance events, current_holder, witnesses
   certifications    ESCS cert events with digest links to Anka
   recalls           active or resolved recalls from ESCS
   end_of_life       recyclable, WEEE category, spare parts, take-back
   access            dpp_url, qr_data (QR code points to dpp_url)
   integrity         anka_audit_url, chain_digest, verified_on_mesh

Vertical profiles:
   electronics_dpp   RoHS + REACH + conflict minerals + WEEE (2028)
   apparel_dpp       GOTS + Fairtrade + ILO labor + Higg carbon (2027)
   battery_dpp       EU Battery Regulation + Verra VCS (2027)
   from_provenance   Generic builder from any Anka audit trail

---

## Adapter API (port 7710)

   POST /events                  publish any supply chain event
   POST /submit_signed           submit pre-signed envelope
   GET  /provenance/:batch_id    provenance query URLs
   GET  /jurisdictions           all 42 known claim spaces
   GET  /events/types            all 18 supported event types
   GET  /health                  service health + node identity

Receipt format:
   { ok, published, witnessed, event_type, batch_id, claim_space,
     digest, issuer_node_id, timestamp_unix_secs, receipt_url }

---

## Provenance Dashboard

   cd sdk/dashboard && python3 proxy.py
   open http://localhost:8080

Times New Roman, navy blue (#0a2d5e), gold accent border (#c8a84b).
Status bar, batch query, breach banner, recall banner, summary grid,
color-coded provenance chain, recall history table.

---

## Test Suite

   tests/test_sc_jurisdictions.fard   35 tests
   tests/test_sc_event.fard           34 tests
   tests/test_sc_oracle.fard          34 tests
   tests/test_sc_policy.fard          57 tests
   tests/test_sc_provenance.fard      32 tests
   tests/test_sc_recall.fard          39 tests
   tests/test_sc_sensor.fard          45 tests
   tests/test_sc_claim.fard           36 tests
   tests/test_sc_bridge.fard          27 tests
   tests/test_sc_live.fard            48 tests
   tests/test_sc_food_live.fard       20 tests
   tests/test_sc_elec_live.fard       22 tests
   tests/test_sc_apparel_live.fard    34 tests
   tests/test_sc_energy_live.fard     38 tests
   tests/test_epcis.fard              41 tests   GS1 EPCIS 2.0
   tests/test_dpp.fard                49 tests   EU DPP
   sdk/python/offline                 40 tests   offline signing
   sdk/node/offline                   38 tests   offline signing
   sdk/go/escs_test.go                15 tests   Go SDK live
   sdk/java/ESCSTest.java             21 tests   Java SDK live
   ─────────────────────────────────────────────────────────────
   total                             669 tests   0 failures

Run FARD tests:   bash run_tests.sh
Run Go tests:     cd sdk/go && go test -v ./...
Run Java tests:   cd sdk/java && java -cp "out:jackson-*.jar" supply.escs.ESCSTest

---

## Docker

   docker compose up anka gatewayd witnessd telemetryd
   docker compose --profile full up   # includes adapter

Services: anka (18080), gatewayd (7700), witnessd (7701),
         telemetryd (7702), adapter (7710)

---

## Source

   src/supply_chain/
     jurisdictions.fard   event.fard        oracle.fard
     policy.fard          provenance.fard   recall.fard
     sensor.fard          claim.fard        bridge.fard

   src/interop/
     epcis.fard           dpp.fard          dpp_verticals.fard

   src/services/
     adapterd.fard        gatewayd.fard
     witnessd.fard        telemetryd.fard

   sdk/
     python/escs.py           python/escs_offline.py
     node/escs.js             node/escs_offline.js
     go/escs.go               go/escs_test.go
     java/ESCSClient.java     java/ESCSTest.java
     openapi/escs.openapi.json
     dashboard/index.html     dashboard/proxy.py

   benchmark/
     load_test.py         BENCHMARK.md      results.json

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

   github.com/mauludsadiq/ESCS   8,600 lines · 669 tests · 31 commits
   github.com/mauludsadiq/EOS    2,948 lines · 143 tests · 12 commits
   github.com/mauludsadiq/Anka   14,506 lines
   github.com/mauludsadiq/Azim   deterministic AI training

---

## License

MUI
