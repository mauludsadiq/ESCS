// Package escs provides a Go client for the ESCS adapter API.
//
// Usage:
//
//client := escs.NewClient("http://localhost:7710")
//receipt, err := client.CustodyTransfer(ctx, escs.CustodyTransferRequest{
//    BatchID:  "batch:LOT-001",
//    From:     "party:producer",
//    To:       "party:shipper",
//    Location: "Chicago, IL",
//    Quantity: 1000,
//    Unit:     "units",
//})
//if err != nil { log.Fatal(err) }
//fmt.Println(receipt.Digest)
//fmt.Println(receipt.Witnessed)
package escs

import (
"bytes"
"context"
"encoding/json"
"fmt"
"io"
"net/http"
"time"
)

// Client is an ESCS adapter HTTP client.
type Client struct {
baseURL    string
httpClient *http.Client
}

// NewClient creates a new ESCS client.
func NewClient(baseURL string) *Client {
return &Client{
baseURL: baseURL,
httpClient: &http.Client{
Timeout: 15 * time.Second,
},
}
}

// Receipt is the response from a successful event publication.
type Receipt struct {
OK                 bool   `json:"ok"`
Published          bool   `json:"published"`
Witnessed          bool   `json:"witnessed"`
EventType          string `json:"event_type"`
BatchID            string `json:"batch_id"`
ClaimSpace         string `json:"claim_space"`
Digest             string `json:"digest"`
IssuerNodeID       string `json:"issuer_node_id"`
TimestampUnixSecs  int64  `json:"timestamp_unix_secs"`
ReceiptURL         string `json:"receipt_url"`
Error              string `json:"reason,omitempty"`
GateResult         *GateResult `json:"gate_result,omitempty"`
}

// GateResult holds gate denial details.
type GateResult struct {
Err string `json:"err"`
}

// Provenance holds provenance query results.
type Provenance struct {
OK       bool     `json:"ok"`
BatchID  string   `json:"batch_id"`
AnkaURL  string   `json:"anka_url"`
Message  string   `json:"message"`
QueryURLs []string `json:"query_urls"`
}

// Health holds service health information.
type Health struct {
OK              bool     `json:"ok"`
Service         string   `json:"service"`
NodeID          string   `json:"node_id"`
AnkaURL         string   `json:"anka_url"`
SupportedEvents []string `json:"supported_events"`
}

// JurisdictionList holds the list of known jurisdictions.
type JurisdictionList struct {
OK            bool     `json:"ok"`
Count         int      `json:"count"`
Jurisdictions []string `json:"jurisdictions"`
}

// EventTypeList holds the list of supported event types.
type EventTypeList struct {
OK         bool     `json:"ok"`
Count      int      `json:"count"`
EventTypes []string `json:"event_types"`
}

// --- Request types ---

type BatchCreatedRequest struct {
BatchID         string `json:"batch_id"`
ProductCode     string `json:"product_code"`
Quantity        int    `json:"quantity"`
Unit            string `json:"unit"`
OriginLocation  string `json:"origin_location"`
ProducerID      string `json:"producer_id"`
LotNumber       string `json:"lot_number"`
ManufactureDate int64  `json:"manufacture_date"`
ExpiryDate      int64  `json:"expiry_date"`
Timestamp       int64  `json:"timestamp_unix_secs,omitempty"`
}

type CustodyTransferRequest struct {
BatchID       string `json:"batch_id"`
From          string `json:"from"`
To            string `json:"to"`
Location      string `json:"location"`
Quantity      int    `json:"quantity"`
Unit          string `json:"unit"`
HandoffMethod string `json:"handoff_method,omitempty"`
ActorID       string `json:"actor_id,omitempty"`
Timestamp     int64  `json:"timestamp_unix_secs,omitempty"`
}

type InspectionPassedRequest struct {
BatchID        string   `json:"batch_id"`
InspectorID    string   `json:"inspector_id"`
InspectionType string   `json:"inspection_type"`
Location       string   `json:"location"`
Standards      []string `json:"standards,omitempty"`
Notes          string   `json:"notes,omitempty"`
Reputation     int      `json:"reputation,omitempty"`
Timestamp      int64    `json:"timestamp_unix_secs,omitempty"`
}

type InspectionFailedRequest struct {
BatchID        string   `json:"batch_id"`
InspectorID    string   `json:"inspector_id"`
InspectionType string   `json:"inspection_type"`
Location       string   `json:"location"`
FailureCodes   []string `json:"failure_codes,omitempty"`
EvidenceRefs   []string `json:"evidence_refs,omitempty"`
Reputation     int      `json:"reputation,omitempty"`
Timestamp      int64    `json:"timestamp_unix_secs,omitempty"`
}

type CustomsClearedRequest struct {
BatchID            string `json:"batch_id"`
CustomsAuthority   string `json:"customs_authority"`
ClearanceRef       string `json:"clearance_ref"`
PortOfEntry        string `json:"port_of_entry"`
DestinationCountry string `json:"destination_country"`
ActorID            string `json:"actor_id,omitempty"`
Reputation         int    `json:"reputation,omitempty"`
Timestamp          int64  `json:"timestamp_unix_secs,omitempty"`
}

type CustomsHeldRequest struct {
BatchID          string   `json:"batch_id"`
CustomsAuthority string   `json:"customs_authority"`
HoldRef          string   `json:"hold_ref"`
PortOfEntry      string   `json:"port_of_entry"`
Reason           string   `json:"reason"`
EvidenceRefs     []string `json:"evidence_refs,omitempty"`
Reputation       int      `json:"reputation,omitempty"`
Timestamp        int64    `json:"timestamp_unix_secs,omitempty"`
}

type TemperatureLogRequest struct {
BatchID      string  `json:"batch_id"`
SensorID     string  `json:"sensor_id"`
Location     string  `json:"location"`
TempMinC     float64 `json:"temp_min_c"`
TempMaxC     float64 `json:"temp_max_c"`
TempAvgC     float64 `json:"temp_avg_c"`
WindowStart  int64   `json:"window_start"`
WindowEnd    int64   `json:"window_end"`
ReadingCount int     `json:"reading_count"`
Reputation   int     `json:"reputation,omitempty"`
Timestamp    int64   `json:"timestamp_unix_secs,omitempty"`
}

type TemperatureBreachRequest struct {
BatchID        string  `json:"batch_id"`
SensorID       string  `json:"sensor_id"`
Location       string  `json:"location"`
TempC          float64 `json:"temp_c"`
ThresholdMinC  float64 `json:"threshold_min_c"`
ThresholdMaxC  float64 `json:"threshold_max_c"`
BreachTimestamp int64  `json:"breach_timestamp"`
DurationSecs   int     `json:"duration_secs"`
EvidenceRef    string  `json:"evidence_ref,omitempty"`
Reputation     int     `json:"reputation,omitempty"`
Timestamp      int64   `json:"timestamp_unix_secs,omitempty"`
}

type CertificationIssuedRequest struct {
BatchID     string `json:"batch_id"`
CertType    string `json:"cert_type"`
CertifierID string `json:"certifier_id"`
CertRef     string `json:"cert_ref"`
ValidFrom   int64  `json:"valid_from"`
ValidUntil  int64  `json:"valid_until"`
Scope       string `json:"scope,omitempty"`
Reputation  int    `json:"reputation,omitempty"`
Timestamp   int64  `json:"timestamp_unix_secs,omitempty"`
}

type CertificationRevokedRequest struct {
BatchID     string   `json:"batch_id"`
CertType    string   `json:"cert_type"`
CertifierID string   `json:"certifier_id"`
CertRef     string   `json:"cert_ref"`
Reason      string   `json:"reason"`
EvidenceRefs []string `json:"evidence_refs,omitempty"`
Reputation  int      `json:"reputation,omitempty"`
Timestamp   int64    `json:"timestamp_unix_secs,omitempty"`
}

type RecallIssuedRequest struct {
RecallID            string   `json:"recall_id"`
AffectedBatchIDs    []string `json:"affected_batch_ids"`
AffectedLotNumbers  []string `json:"affected_lot_numbers"`
ProductCode         string   `json:"product_code"`
Severity            string   `json:"severity"`
Reason              string   `json:"reason"`
IssuerID            string   `json:"issuer_id"`
Instructions        string   `json:"instructions"`
RegulatoryRef       string   `json:"regulatory_ref"`
Reputation          int      `json:"reputation,omitempty"`
Timestamp           int64    `json:"timestamp_unix_secs,omitempty"`
}

type RecallAcknowledgedRequest struct {
RecallID     string `json:"recall_id"`
BatchID      string `json:"batch_id"`
HolderID     string `json:"holder_id"`
QuantityHeld int    `json:"quantity_held"`
Location     string `json:"location"`
ActionPlan   string `json:"action_plan"`
Timestamp    int64  `json:"timestamp_unix_secs,omitempty"`
}

type RecallResolvedRequest struct {
RecallID          string   `json:"recall_id"`
BatchID           string   `json:"batch_id"`
HolderID          string   `json:"holder_id"`
Resolution        string   `json:"resolution"`
QuantityDestroyed int      `json:"quantity_destroyed"`
QuantityReturned  int      `json:"quantity_returned"`
EvidenceRefs      []string `json:"evidence_refs,omitempty"`
Timestamp         int64    `json:"timestamp_unix_secs,omitempty"`
}

type SensorReadingRequest struct {
BatchID      string  `json:"batch_id"`
SensorID     string  `json:"sensor_id"`
SensorType   string  `json:"sensor_type"`
Location     string  `json:"location"`
Value        float64 `json:"value"`
Unit         string  `json:"unit"`
ThresholdMin float64 `json:"threshold_min"`
ThresholdMax float64 `json:"threshold_max"`
InRange      bool    `json:"in_range"`
Reputation   int     `json:"reputation,omitempty"`
Timestamp    int64   `json:"timestamp_unix_secs,omitempty"`
}

type LocationUpdateRequest struct {
BatchID    string                 `json:"batch_id"`
ActorID    string                 `json:"actor_id"`
Location   string                 `json:"location"`
Coordinates map[string]float64   `json:"coordinates,omitempty"`
FacilityID string                 `json:"facility_id,omitempty"`
ScanMethod string                 `json:"scan_method,omitempty"`
Timestamp  int64                  `json:"timestamp_unix_secs,omitempty"`
}

type OriginAttestedRequest struct {
BatchID         string   `json:"batch_id"`
CertifierID     string   `json:"certifier_id"`
CountryOfOrigin string   `json:"country_of_origin"`
Region          string   `json:"region,omitempty"`
FacilityID      string   `json:"facility_id,omitempty"`
Standards       []string `json:"standards,omitempty"`
EvidenceRefs    []string `json:"evidence_refs,omitempty"`
Reputation      int      `json:"reputation,omitempty"`
Timestamp       int64    `json:"timestamp_unix_secs,omitempty"`
}

// --- HTTP helpers ---

func (c *Client) post(ctx context.Context, path string, body interface{}) (*Receipt, error) {
b, err := json.Marshal(body)
if err != nil {
return nil, fmt.Errorf("marshal: %w", err)
}
req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(b))
if err != nil {
return nil, err
}
req.Header.Set("Content-Type", "application/json")
resp, err := c.httpClient.Do(req)
if err != nil {
return nil, fmt.Errorf("request: %w", err)
}
defer resp.Body.Close()
data, _ := io.ReadAll(resp.Body)
var r Receipt
if err := json.Unmarshal(data, &r); err != nil {
return nil, fmt.Errorf("decode: %w", err)
}
return &r, nil
}

func (c *Client) get(ctx context.Context, path string, out interface{}) error {
req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+path, nil)
if err != nil {
return err
}
resp, err := c.httpClient.Do(req)
if err != nil {
return fmt.Errorf("request: %w", err)
}
defer resp.Body.Close()
data, _ := io.ReadAll(resp.Body)
return json.Unmarshal(data, out)
}

func now() int64 { return time.Now().Unix() }

func ts(t int64) int64 {
if t == 0 {
return now()
}
return t
}


// --- Getters for Health ---
func (h *Health) IsOk() bool { return h.OK }
func (h *Health) GetService() string { return h.Service }
func (h *Health) GetNodeID() string { return h.NodeID }
func (h *Health) GetAnkaURL() string { return h.AnkaURL }
func (h *Health) GetSupportedEvents() []string { return h.SupportedEvents }

// --- Event methods ---

func (c *Client) BatchCreated(ctx context.Context, r BatchCreatedRequest) (*Receipt, error) {
type req struct {
BatchCreatedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "batch_created"})
}

func (c *Client) CustodyTransfer(ctx context.Context, r CustodyTransferRequest) (*Receipt, error) {
type req struct {
CustodyTransferRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "custody_transfer"})
}

func (c *Client) InspectionPassed(ctx context.Context, r InspectionPassedRequest) (*Receipt, error) {
type req struct {
InspectionPassedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "inspection_passed"})
}

func (c *Client) InspectionFailed(ctx context.Context, r InspectionFailedRequest) (*Receipt, error) {
type req struct {
InspectionFailedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "inspection_failed"})
}

func (c *Client) CustomsCleared(ctx context.Context, r CustomsClearedRequest) (*Receipt, error) {
type req struct {
CustomsClearedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "customs_cleared"})
}

func (c *Client) CustomsHeld(ctx context.Context, r CustomsHeldRequest) (*Receipt, error) {
type req struct {
CustomsHeldRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "customs_held"})
}

func (c *Client) TemperatureLog(ctx context.Context, r TemperatureLogRequest) (*Receipt, error) {
type req struct {
TemperatureLogRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "temperature_log"})
}

func (c *Client) TemperatureBreach(ctx context.Context, r TemperatureBreachRequest) (*Receipt, error) {
type req struct {
TemperatureBreachRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "temperature_breach"})
}

func (c *Client) CertificationIssued(ctx context.Context, r CertificationIssuedRequest) (*Receipt, error) {
type req struct {
CertificationIssuedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "certification_issued"})
}

func (c *Client) CertificationRevoked(ctx context.Context, r CertificationRevokedRequest) (*Receipt, error) {
type req struct {
CertificationRevokedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "certification_revoked"})
}

func (c *Client) RecallIssued(ctx context.Context, r RecallIssuedRequest) (*Receipt, error) {
type req struct {
RecallIssuedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "recall_issued"})
}

func (c *Client) RecallAcknowledged(ctx context.Context, r RecallAcknowledgedRequest) (*Receipt, error) {
type req struct {
RecallAcknowledgedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "recall_acknowledged"})
}

func (c *Client) RecallResolved(ctx context.Context, r RecallResolvedRequest) (*Receipt, error) {
type req struct {
RecallResolvedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "recall_resolved"})
}

func (c *Client) SensorReading(ctx context.Context, r SensorReadingRequest) (*Receipt, error) {
type req struct {
SensorReadingRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "sensor_reading"})
}

func (c *Client) LocationUpdate(ctx context.Context, r LocationUpdateRequest) (*Receipt, error) {
type req struct {
LocationUpdateRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "location_update"})
}

func (c *Client) OriginAttested(ctx context.Context, r OriginAttestedRequest) (*Receipt, error) {
type req struct {
OriginAttestedRequest
EventType string `json:"event_type"`
}
r.Timestamp = ts(r.Timestamp)
return c.post(ctx, "/events", req{r, "origin_attested"})
}


// BatchRequest is a list of events to publish concurrently.
type BatchRequest struct {
Events []interface{} `json:"events"`
}

// BatchReceipt is the response from a batch publish.
type BatchReceipt struct {
OK        bool      `json:"ok"`
Total     int       `json:"total"`
Succeeded int       `json:"succeeded"`
Failed    int       `json:"failed"`
Receipts  []Receipt `json:"receipts"`
}


// Batch publishes multiple events concurrently via POST /events/batch.
// Up to 100 events per call. Returns receipts in submission order.
func (c *Client) Batch(ctx context.Context, events []interface{}) (*BatchReceipt, error) {
b, err := json.Marshal(map[string]interface{}{"events": events})
if err != nil {
return nil, fmt.Errorf("marshal: %w", err)
}
req, err := http.NewRequestWithContext(ctx, http.MethodPost,
c.baseURL+"/events/batch", bytes.NewReader(b))
if err != nil {
return nil, err
}
req.Header.Set("Content-Type", "application/json")
resp, err := c.httpClient.Do(req)
if err != nil {
return nil, fmt.Errorf("request: %w", err)
}
defer resp.Body.Close()
data, _ := io.ReadAll(resp.Body)
var r BatchReceipt
if err := json.Unmarshal(data, &r); err != nil {
return nil, fmt.Errorf("decode: %w", err)
}
return &r, nil
}

// --- Provenance queries ---

func (c *Client) Provenance(ctx context.Context, batchID string) (*Provenance, error) {
var p Provenance
err := c.get(ctx, "/provenance/"+batchID, &p)
return &p, err
}

// --- Discovery ---

func (c *Client) Health(ctx context.Context) (*Health, error) {
var h Health
err := c.get(ctx, "/health", &h)
return &h, err
}

func (c *Client) Jurisdictions(ctx context.Context) (*JurisdictionList, error) {
var j JurisdictionList
err := c.get(ctx, "/jurisdictions", &j)
return &j, err
}

func (c *Client) EventTypes(ctx context.Context) (*EventTypeList, error) {
var e EventTypeList
err := c.get(ctx, "/events/types", &e)
return &e, err
}
