package escs_test

import (
"context"
"testing"
"time"

escs "github.com/mauludsadiq/ESCS/sdk/go"
)

var client = escs.NewClient("http://localhost:7710")
var ctx = context.Background()
var now = time.Now().Unix()

func TestHealth(t *testing.T) {
h, err := client.Health(ctx)
if err != nil {
t.Fatalf("health check failed: %v", err)
}
if !h.IsOk() {
t.Fatal("health not ok")
}
if h.GetService() == "" {
t.Fatal("missing service name")
}
t.Logf("node: %s", h.GetNodeID()[:20])
}

func TestJurisdictions(t *testing.T) {
j, err := client.Jurisdictions(ctx)
if err != nil {
t.Fatalf("jurisdictions failed: %v", err)
}
if j.Count != 42 {
t.Fatalf("expected 42 jurisdictions, got %d", j.Count)
}
}

func TestEventTypes(t *testing.T) {
e, err := client.EventTypes(ctx)
if err != nil {
t.Fatalf("event types failed: %v", err)
}
if e.Count != 18 {
t.Fatalf("expected 18 event types, got %d", e.Count)
}
}

func TestBatchCreated(t *testing.T) {
r, err := client.BatchCreated(ctx, escs.BatchCreatedRequest{
BatchID:         "batch:GO-TEST-001",
ProductCode:     "DRUG-001",
Quantity:        1000,
Unit:            "units",
OriginLocation:  "Chicago, IL",
ProducerID:      "party:producer",
LotNumber:       "LOT-GO-001",
ManufactureDate: now,
ExpiryDate:      now + 31536000,
})
if err != nil {
t.Fatalf("batch_created failed: %v", err)
}
if !r.OK {
t.Fatalf("not ok: %s", r.Error)
}
if !r.Published {
t.Fatal("not published")
}
if !r.Witnessed {
t.Fatal("not witnessed")
}
if r.Digest == "" {
t.Fatal("missing digest")
}
t.Logf("digest: %s", r.Digest[:20])
}

func TestCustodyTransfer(t *testing.T) {
r, err := client.CustodyTransfer(ctx, escs.CustodyTransferRequest{
BatchID:  "batch:GO-TEST-001",
From:     "party:producer",
To:       "party:shipper",
Location: "Chicago, IL",
Quantity: 1000,
Unit:     "units",
})
if err != nil {
t.Fatalf("custody_transfer failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
if r.ClaimSpace != "SUPPLY.CUSTODY.v1" {
t.Fatalf("wrong claim_space: %s", r.ClaimSpace)
}
}

func TestInspectionPassed(t *testing.T) {
r, err := client.InspectionPassed(ctx, escs.InspectionPassedRequest{
BatchID:        "batch:GO-TEST-001",
InspectorID:    "inspector:fda-001",
InspectionType: "fda_gmp",
Location:       "Chicago, IL",
Standards:      []string{"FDA-21CFR"},
Notes:          "all clear",
Reputation:     5,
})
if err != nil {
t.Fatalf("inspection_passed failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestInspectionGateDenied(t *testing.T) {
r, err := client.InspectionPassed(ctx, escs.InspectionPassedRequest{
BatchID:        "batch:GO-TEST-001",
InspectorID:    "inspector:fda-001",
InspectionType: "fda_gmp",
Location:       "Chicago, IL",
Reputation:     4, // below RepMin(5)
})
if err != nil {
t.Fatalf("request failed: %v", err)
}
if r.Published {
t.Fatal("should have been gate denied at rep=4")
}
}

func TestCustomsCleared(t *testing.T) {
r, err := client.CustomsCleared(ctx, escs.CustomsClearedRequest{
BatchID:            "batch:GO-TEST-001",
CustomsAuthority:   "CBP",
ClearanceRef:       "CBP-GO-TEST-001",
PortOfEntry:        "JFK",
DestinationCountry: "US",
Reputation:         10,
})
if err != nil {
t.Fatalf("customs_cleared failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestTemperatureLog(t *testing.T) {
tsNow := time.Now().Unix()
r, err := client.TemperatureLog(ctx, escs.TemperatureLogRequest{
BatchID:      "batch:GO-TEST-001",
SensorID:     "sensor:cold-007",
Location:     "Chicago Cold Storage",
TempMinC:     2.1,
TempMaxC:     7.8,
TempAvgC:     4.5,
WindowStart:  tsNow - 299,
WindowEnd:    tsNow,
ReadingCount: 60,
Reputation:   1,
Timestamp:    tsNow,
})
if err != nil {
t.Fatalf("temperature_log failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestTemperatureBreach(t *testing.T) {
r, err := client.TemperatureBreach(ctx, escs.TemperatureBreachRequest{
BatchID:         "batch:GO-TEST-001",
SensorID:        "sensor:cold-007",
Location:        "Chicago Cold Storage",
TempC:           11.2,
ThresholdMinC:   2.0,
ThresholdMaxC:   8.0,
BreachTimestamp: now - 600,
DurationSecs:    600,
Reputation:      1,
})
if err != nil {
t.Fatalf("temperature_breach failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestCertificationIssued(t *testing.T) {
r, err := client.CertificationIssued(ctx, escs.CertificationIssuedRequest{
BatchID:     "batch:GO-TEST-001",
CertType:    "fda_gmp",
CertifierID: "certifier:fda-001",
CertRef:     "FDA-GMP-GO-001",
ValidFrom:   now,
ValidUntil:  now + 31536000,
Reputation:  20,
})
if err != nil {
t.Fatalf("certification_issued failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestRecallIssued(t *testing.T) {
r, err := client.RecallIssued(ctx, escs.RecallIssuedRequest{
RecallID:           "recall:GO-TEST-001",
AffectedBatchIDs:   []string{"batch:GO-TEST-001"},
AffectedLotNumbers: []string{"LOT-GO-001"},
ProductCode:        "DRUG-001",
Severity:           "class_i",
Reason:             "go sdk test recall",
IssuerID:           "oracle:fda-001",
Instructions:       "destroy",
RegulatoryRef:      "FDA-GO-2025-001",
Reputation:         50,
})
if err != nil {
t.Fatalf("recall_issued failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestRecallGateDenied(t *testing.T) {
r, err := client.RecallIssued(ctx, escs.RecallIssuedRequest{
RecallID:           "recall:GO-TEST-002",
AffectedBatchIDs:   []string{"batch:GO-TEST-001"},
AffectedLotNumbers: []string{"LOT-GO-001"},
ProductCode:        "DRUG-001",
Severity:           "class_i",
Reason:             "should be denied",
IssuerID:           "oracle:fda-001",
Instructions:       "destroy",
RegulatoryRef:      "FDA-GO-2025-002",
Reputation:         49, // below RepMin(50)
})
if err != nil {
t.Fatalf("request failed: %v", err)
}
if r.Published {
t.Fatal("should have been gate denied at rep=49")
}
}

func TestOriginAttested(t *testing.T) {
r, err := client.OriginAttested(ctx, escs.OriginAttestedRequest{
BatchID:         "batch:GO-TEST-001",
CertifierID:     "certifier:origin-001",
CountryOfOrigin: "US",
Region:          "Illinois",
Standards:       []string{"FDA-21CFR"},
Reputation:      10,
})
if err != nil {
t.Fatalf("origin_attested failed: %v", err)
}
if !r.OK || !r.Published {
t.Fatalf("not published: %s", r.Error)
}
}

func TestProvenance(t *testing.T) {
p, err := client.Provenance(ctx, "batch:GO-TEST-001")
if err != nil {
t.Fatalf("provenance failed: %v", err)
}
if !p.OK {
t.Fatal("provenance not ok")
}
if p.BatchID != "batch:GO-TEST-001" {
t.Fatalf("wrong batch_id: %s", p.BatchID)
}
}
