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

   8,630 lines of FARD
     555 FARD tests, 0 failures
      40 Python offline signing tests
      38 Node.js offline signing tests
      16 Go SDK tests (incl. batch)
      21 Java SDK tests
     670 total tests, 0 failures
      34 commits
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
       1 batch endpoint (POST /events/batch)
       1 load test + benchmark

---

## Quickstart

   # Start the stack
   docker compose up anka gatewayd witnessd adapterd

   # Single event
   curl -X POST http://localhost:7710/events \
     -H "Content-Type: application/json" \
     -d '{"event_type":"custody_transfer","batch_id":"batch:LOT-001",
           "from":"party:producer","to":"party:shipper",
           "location":"Chicago, IL","quantity":1000,"unit":"units"}'

   # Batch (concurrent, 2-2.3x throughput)
   curl -X POST http://localhost:7710/events/batch \
     -H "Content-Type: application/json" \
     -d '{"events":[
       {"event_type":"batch_created","batch_id":"batch:LOT-001",...},
       {"event_type":"custody_transfer","batch_id":"batch:LOT-001",...},
       {"event_type":"inspection_passed","batch_id":"batch:LOT-001",...}
     ]}'

   # Response
   {
     "ok": true,
     "total": 3,
     "succeeded": 3,
     "failed": 0,
     "receipts": [
       { "ok": true, "published": true, "witnessed": true,
         "digest": "sha256:...", "receipt_url": "http://..." },
       ...
     ]
   }

---

## Performance

### Current (fardrun v1.7.0, tree-walking interpreter)

   Offline signing         9,286 signs/sec   p50=0.106ms
   Single event            ~5.5s/event        0.18 eps
   Batch 3 events          ~8.4s              0.36 eps  (2x vs sequential)
   Batch 5 events          ~11.7s             0.43 eps  (2.3x)
   10 concurrent requests  ~31s               (vs 55s sequential)

   Root cause: AST evaluation ~5s/request in interpreter mode.
   Gate evaluation, policy compilation, signing all take <1ms.
   Bottleneck is fardrun net.serve evaluating the handler expression tree.

### Improvements shipped

   Async witnessing    promise.spawn — receipt returned after Anka publish,
                       witness runs in background thread. No blocking.

   Thread-per-request  net.serve now spawns a thread per request.
                       Module cache pre-warmed at startup (60 modules).
                       Concurrent requests no longer queue behind each other.

   Batch endpoint      POST /events/batch — promise.spawn_ordered publishes
                       all events in parallel. 2-2.3x throughput improvement.

### Performance roadmap

   fardrun v1.7.0 (interpreter)    ~5s/request     current
   fardrun Stage 2 (bytecode)      ~100-500ms       10-50x faster
   fardrun Stage 5 (native)        ~5-50ms          100-1000x faster

ESCS is architecturally correct for production. The policy model,
async witnessing, batch publish, and offline signing are all production-ready.
Performance follows the FARD self-hosting roadmap.

### Offline signing is not affected by interpreter overhead

Offline signing runs entirely in Python/Node.js at 9,286 signs/sec.
For high-throughput deployments: sign locally, queue, submit in batches.
The adapter becomes a low-frequency settlement layer.

---

## Client SDKs

### Python

   pip install requests cryptography

   from escs import ESCSClient
   client = ESCSClient("http://localhost:7710")

   # Single event
   r = client.custody_transfer(
       batch_id="batch:LOT-001", from_party="party:a",
       to_party="party:b", location="Chicago", quantity=1000, unit="units"
   )
   print(r.digest, r.witnessed)

   # Batch (concurrent)
   result = client.batch([
       {"event_type": "batch_created", "batch_id": "batch:LOT-001", ...},
       {"event_type": "custody_transfer", "batch_id": "batch:LOT-001", ...},
   ])
   print(result["succeeded"], "/", result["total"])

### Node.js (Node 18+, no dependencies)

   const { ESCSClient } = require("./escs")
   const client = new ESCSClient("http://localhost:7710")

   // Single
   const r = await client.custodyTransfer({ batchId: "batch:LOT-001", ... })

   // Batch
   const result = await client.batch([
       { event_type: "batch_created", batch_id: "batch:LOT-001", ... },
       { event_type: "custody_transfer", batch_id: "batch:LOT-001", ... },
   ])

### Go

   client := escs.NewClient("http://localhost:7710")

   // Single
   r, err := client.CustodyTransfer(ctx, escs.CustodyTransferRequest{...})

   // Batch
   result, err := client.Batch(ctx, []interface{}{
       map[string]interface{}{"event_type": "custody_transfer", ...},
       map[string]interface{}{"event_type": "inspection_passed", ...},
   })
   fmt.Println(result.Succeeded, "/", result.Total)

### Java (Java 11+, jackson-databind)

   ESCSClient client = new ESCSClient("http://127.0.0.1:7710");
   Receipt r = client.custodyTransfer(
       ESCSClient.CustodyTransferRequest.builder()
           .batchId("batch:LOT-001").from("party:a").to("party:b")
           .location("Chicago").quantity(1000).unit("units").build()
   );

### OpenAPI

   sdk/openapi/escs.openapi.json — OpenAPI 3.0.3 specification
   openapi-generator generate -i escs.openapi.json -g rust -o sdk/rust

---

## Offline Signing

Sign events locally without the adapter. The adapter becomes optional.

   from escs_offline import OfflineSigner, OfflineQueue

   signer = OfflineSigner.generate("my-institution-seed")
   envelope = signer.sign_event({
       "event_type": "custody_transfer",
       "batch_id": "batch:LOT-001", ...
   })
   print(envelope.digest)    # sha256:... — signed locally, 9,286/sec
   print(envelope.published) # False — not yet on Anka

   # Queue for later
   queue = OfflineQueue("queue.jsonl")
   queue.enqueue(envelope)

   # Submit when online
   client = ESCSClient("http://localhost:7710")
   receipt = client.submit_signed(envelope)
   print(receipt.published, receipt.witnessed)

Architecture:
   Before: institution -> adapter -> sign -> gate -> Anka
   After:  institution -> SDK keypair -> sign (9,286/sec) -> queue
                                                               |
                                                    when online:
                                             /submit_signed -> gate -> Anka

---

## Architecture

   Institution A          Institution B          Institution C
        |                      |                      |
   POST /events           POST /events/batch     POST /submit_signed
   (single)               (concurrent)           (pre-signed)
        |                      |                      |
        +------------- adapterd (port 7710) ----------+
                               |
                   keypair + signing + gate eval
                   promise.spawn_ordered (batch)
                   async witness (fire and forget)
                               |
                       Anka mesh publish
                               |
                   witness (background thread)
                               |
                   permanent audit trail
                               |
                   Dashboard · EPCIS export · DPP assembly

---

## Verticals

### Pharmaceutical
FDA DSCSA, EU FMD, WHO/FDA cold chain (2-8C, 1hr freshness), PMDA,
ANVISA, MHRA. Recalls require RepMin(50). Live: batch → cold chain →
breach → JFK customs → Class I recall → 10,000 units destroyed.
9 events, 11 witnesses.

### Food
FSMA, EU food safety, cold chain (0-4C), USDA Organic, Halal, Kosher.
Live: organic spinach Salinas Valley → USDA organic → FSMA → Class I
E. coli recall.

### Electronics
EU REACH, RoHS, conflict minerals (Dodd-Frank 1502), WEEE, origin.
Live: TSMC Taiwan → Singapore → EU customs Hamburg, 3 certifications.

### Apparel
ILO/SA8000 labor, country of origin, GOTS organic, Fairtrade.
Live: Bangladesh → UK customs Felixstowe → Amsterdam, 9 events.

### Energy
REC, Verra VCS carbon, grid provenance, ISO 50001.
Live: Horns Rev 3 Denmark, 50,000 MWh → Germany via ACER.

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
   SUPPLY.CUSTODY.v1       RepMin(0)
   SUPPLY.INSPECTION.v1    RepMin(5)
   SUPPLY.SENSOR.v1        RepMin(1)  + AgeMax(300)
   SUPPLY.RECALL.v1        RepMin(50)
   SUPPLY.ISO9001.v1       RepMin(20)
   SUPPLY.ISO28000.v1      RepMin(20)
   SUPPLY.CUSTOMS.US.v1    RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.EU.v1    RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.UK.v1    RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.CN.v1    RepMin(10) + AgeMax(86400)
   SUPPLY.CUSTOMS.JP.v1    RepMin(10) + AgeMax(86400)
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

   RepMin(n)       ctx.reputation >= n
   AgeMax(secs)    now - claim.timestamp <= secs
   JurAllow([...]) claim.claim_space in allowed list

   recall_policy         RepMin(50)
   certification_policy  RepMin(20)
   pharma/customs        RepMin(10-20) + AgeMax(86400)
   cold_chain            RepMin(10) + AgeMax(3600)
   inspection            RepMin(5)
   sensor                RepMin(1) + AgeMax(300)
   custody               RepMin(0)

---

## GS1 EPCIS 2.0 Bridge

All 18 ESCS events map to EPCIS 2.0 (ObjectEvent, TransactionEvent,
sensorElementList, certificationList). Bidirectional — any EPCIS 2.0
document can be ingested and converted to ESCS events with cryptographic
receipts. ESCS sits underneath SAP, IBM Food Trust, TraceLink.

---

## EU Digital Product Passport

EU ESPR compliant DPP assembled from Anka audit trail.

   Mandate: apparel/energy 2027, electronics 2028, pharma/food 2029

   Profiles: electronics_dpp (RoHS+REACH+WEEE+conflict minerals)
             apparel_dpp (GOTS+Fairtrade+ILO labor)
             battery_dpp (EU Battery Regulation + Verra VCS)
             from_provenance (generic, any vertical)

---

## Adapter API (port 7710)

   POST /events                  publish single event
   POST /events/batch            publish array of events (concurrent)
   POST /submit_signed           submit pre-signed envelope
   GET  /provenance/:batch_id    provenance query URLs
   GET  /jurisdictions           all 42 claim spaces
   GET  /events/types            all 18 event types
   GET  /health                  service health + node identity

Batch response: { ok, total, succeeded, failed, receipts: [...] }
Single receipt: { ok, published, witnessed, digest, receipt_url, ... }

---

## Test Suite

   tests/test_sc_jurisdictions.fard   35
   tests/test_sc_event.fard           34
   tests/test_sc_oracle.fard          34
   tests/test_sc_policy.fard          57
   tests/test_sc_provenance.fard      32
   tests/test_sc_recall.fard          39
   tests/test_sc_sensor.fard          45
   tests/test_sc_claim.fard           36
   tests/test_sc_bridge.fard          27
   tests/test_sc_live.fard            48
   tests/test_sc_food_live.fard       20
   tests/test_sc_elec_live.fard       22
   tests/test_sc_apparel_live.fard    34
   tests/test_sc_energy_live.fard     38
   tests/test_epcis.fard              41   GS1 EPCIS 2.0
   tests/test_dpp.fard                49   EU DPP
   sdk/python/offline                 40   offline signing
   sdk/node/offline                   38   offline signing
   sdk/go/escs_test.go                16   Go SDK (incl. batch)
   sdk/java/ESCSTest.java             21   Java SDK
   ─────────────────────────────────────────────────────────────
   total                             670   0 failures

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

## Docker

   docker compose up anka gatewayd witnessd telemetryd
   docker compose --profile full up

   anka (18080)  gatewayd (7700)  witnessd (7701)
   telemetryd (7702)  adapter (7710)

---

## Stack

   ESCS       supply chain provenance   this repo
   EOS        epistemic kernel          claims, gates, witnesses
   Anka       coordination mesh         publish, audit, discover
   Azim       deterministic AI          receipts as claims
   Fard Dinar monetary protocol         transactions as claims
   FARD       language + runtime        deterministic, receipted

---

## Repositories

   github.com/mauludsadiq/ESCS   8,630 lines · 670 tests · 34 commits
   github.com/mauludsadiq/EOS    2,948 lines · 143 tests
   github.com/mauludsadiq/Anka   14,506 lines
   github.com/mauludsadiq/FARD   net.serve threading + cache warmup

---

## License

MUI
