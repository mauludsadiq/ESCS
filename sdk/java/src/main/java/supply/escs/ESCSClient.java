package supply.escs;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * ESCS Java SDK — thin wrapper around the ESCS adapter HTTP API.
 *
 * <pre>{@code
 * ESCSClient client = new ESCSClient("http://localhost:7710");
 *
 * Receipt r = client.custodyTransfer(CustodyTransferRequest.builder()
 *     .batchId("batch:LOT-001")
 *     .from("party:producer")
 *     .to("party:shipper")
 *     .location("Chicago, IL")
 *     .quantity(1000)
 *     .unit("units")
 *     .build());
 *
 * System.out.println(r.getDigest());
 * System.out.println(r.isWitnessed());
 * }</pre>
 */
public class ESCSClient {

    private final String baseUrl;
    private final HttpClient http;
    private final ObjectMapper mapper;

    public ESCSClient(String baseUrl) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
        this.mapper = new ObjectMapper();
    }

    // --- Response types ---

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Receipt {
        private boolean ok;
        private boolean published;
        private boolean witnessed;
        @JsonProperty("event_type") private String eventType;
        @JsonProperty("batch_id") private String batchId;
        @JsonProperty("claim_space") private String claimSpace;
        private String digest;
        @JsonProperty("issuer_node_id") private String issuerNodeId;
        @JsonProperty("timestamp_unix_secs") private long timestampUnixSecs;
        @JsonProperty("receipt_url") private String receiptUrl;
        private String reason;

        public boolean isOk() { return ok; }
        public boolean isPublished() { return published; }
        public boolean isWitnessed() { return witnessed; }
        public String getEventType() { return eventType; }
        public String getBatchId() { return batchId; }
        public String getClaimSpace() { return claimSpace; }
        public String getDigest() { return digest; }
        public String getIssuerNodeId() { return issuerNodeId; }
        public long getTimestampUnixSecs() { return timestampUnixSecs; }
        public String getReceiptUrl() { return receiptUrl; }
        public String getReason() { return reason; }

        @Override public String toString() {
            return String.format("Receipt(ok=%s, digest=%s, witnessed=%s)",
                ok, digest != null ? digest.substring(0, Math.min(20, digest.length())) + "..." : "null", witnessed);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Health {
        private boolean ok;
        private String service;
        @JsonProperty("node_id") private String nodeId;
        @JsonProperty("anka_url") private String ankaUrl;
        @JsonProperty("supported_events") private List<String> supportedEvents;

        public boolean isOk() { return ok; }
        public String getService() { return service; }
        public String getNodeId() { return nodeId; }
        public String getAnkaUrl() { return ankaUrl; }
        public List<String> getSupportedEvents() { return supportedEvents; }
    }

    // --- Request builders ---

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class CustodyTransferRequest {
        @JsonProperty("event_type") public final String eventType = "custody_transfer";
        @JsonProperty("batch_id") public String batchId;
        public String from;
        public String to;
        public String location;
        public int quantity;
        public String unit;
        @JsonProperty("handoff_method") public String handoffMethod;
        @JsonProperty("actor_id") public String actorId;
        @JsonProperty("timestamp_unix_secs") public long timestamp;

        public static Builder builder() { return new Builder(); }
        public static class Builder {
            private final CustodyTransferRequest r = new CustodyTransferRequest();
            public Builder batchId(String v) { r.batchId = v; return this; }
            public Builder from(String v) { r.from = v; return this; }
            public Builder to(String v) { r.to = v; return this; }
            public Builder location(String v) { r.location = v; return this; }
            public Builder quantity(int v) { r.quantity = v; return this; }
            public Builder unit(String v) { r.unit = v; return this; }
            public Builder handoffMethod(String v) { r.handoffMethod = v; return this; }
            public Builder actorId(String v) { r.actorId = v; return this; }
            public Builder timestamp(long v) { r.timestamp = v; return this; }
            public CustodyTransferRequest build() {
                if (r.timestamp == 0) r.timestamp = Instant.now().getEpochSecond();
                return r;
            }
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class BatchCreatedRequest {
        @JsonProperty("event_type") public final String eventType = "batch_created";
        @JsonProperty("batch_id") public String batchId;
        @JsonProperty("product_code") public String productCode;
        public int quantity;
        public String unit;
        @JsonProperty("origin_location") public String originLocation;
        @JsonProperty("producer_id") public String producerId;
        @JsonProperty("lot_number") public String lotNumber;
        @JsonProperty("manufacture_date") public long manufactureDate;
        @JsonProperty("expiry_date") public long expiryDate;
        @JsonProperty("timestamp_unix_secs") public long timestamp;

        public static Builder builder() { return new Builder(); }
        public static class Builder {
            private final BatchCreatedRequest r = new BatchCreatedRequest();
            public Builder batchId(String v) { r.batchId = v; return this; }
            public Builder productCode(String v) { r.productCode = v; return this; }
            public Builder quantity(int v) { r.quantity = v; return this; }
            public Builder unit(String v) { r.unit = v; return this; }
            public Builder originLocation(String v) { r.originLocation = v; return this; }
            public Builder producerId(String v) { r.producerId = v; return this; }
            public Builder lotNumber(String v) { r.lotNumber = v; return this; }
            public Builder manufactureDate(long v) { r.manufactureDate = v; return this; }
            public Builder expiryDate(long v) { r.expiryDate = v; return this; }
            public Builder timestamp(long v) { r.timestamp = v; return this; }
            public BatchCreatedRequest build() {
                if (r.timestamp == 0) r.timestamp = Instant.now().getEpochSecond();
                return r;
            }
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class RecallIssuedRequest {
        @JsonProperty("event_type") public final String eventType = "recall_issued";
        @JsonProperty("recall_id") public String recallId;
        @JsonProperty("affected_batch_ids") public List<String> affectedBatchIds;
        @JsonProperty("affected_lot_numbers") public List<String> affectedLotNumbers;
        @JsonProperty("product_code") public String productCode;
        public String severity;
        public String reason;
        @JsonProperty("issuer_id") public String issuerId;
        public String instructions;
        @JsonProperty("regulatory_ref") public String regulatoryRef;
        public int reputation;
        @JsonProperty("timestamp_unix_secs") public long timestamp;

        public static Builder builder() { return new Builder(); }
        public static class Builder {
            private final RecallIssuedRequest r = new RecallIssuedRequest();
            public Builder recallId(String v) { r.recallId = v; return this; }
            public Builder affectedBatchIds(List<String> v) { r.affectedBatchIds = v; return this; }
            public Builder affectedLotNumbers(List<String> v) { r.affectedLotNumbers = v; return this; }
            public Builder productCode(String v) { r.productCode = v; return this; }
            public Builder severity(String v) { r.severity = v; return this; }
            public Builder reason(String v) { r.reason = v; return this; }
            public Builder issuerId(String v) { r.issuerId = v; return this; }
            public Builder instructions(String v) { r.instructions = v; return this; }
            public Builder regulatoryRef(String v) { r.regulatoryRef = v; return this; }
            public Builder reputation(int v) { r.reputation = v; return this; }
            public Builder timestamp(long v) { r.timestamp = v; return this; }
            public RecallIssuedRequest build() {
                if (r.timestamp == 0) r.timestamp = Instant.now().getEpochSecond();
                if (r.reputation == 0) r.reputation = 50;
                return r;
            }
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class CustomsClearedRequest {
        @JsonProperty("event_type") public final String eventType = "customs_cleared";
        @JsonProperty("batch_id") public String batchId;
        @JsonProperty("customs_authority") public String customsAuthority;
        @JsonProperty("clearance_ref") public String clearanceRef;
        @JsonProperty("port_of_entry") public String portOfEntry;
        @JsonProperty("destination_country") public String destinationCountry;
        @JsonProperty("actor_id") public String actorId;
        public int reputation;
        @JsonProperty("timestamp_unix_secs") public long timestamp;

        public static Builder builder() { return new Builder(); }
        public static class Builder {
            private final CustomsClearedRequest r = new CustomsClearedRequest();
            public Builder batchId(String v) { r.batchId = v; return this; }
            public Builder customsAuthority(String v) { r.customsAuthority = v; return this; }
            public Builder clearanceRef(String v) { r.clearanceRef = v; return this; }
            public Builder portOfEntry(String v) { r.portOfEntry = v; return this; }
            public Builder destinationCountry(String v) { r.destinationCountry = v; return this; }
            public Builder reputation(int v) { r.reputation = v; return this; }
            public Builder timestamp(long v) { r.timestamp = v; return this; }
            public CustomsClearedRequest build() {
                if (r.timestamp == 0) r.timestamp = Instant.now().getEpochSecond();
                if (r.reputation == 0) r.reputation = 10;
                return r;
            }
        }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class TemperatureLogRequest {
        @JsonProperty("event_type") public final String eventType = "temperature_log";
        @JsonProperty("batch_id") public String batchId;
        @JsonProperty("sensor_id") public String sensorId;
        public String location;
        @JsonProperty("temp_min_c") public double tempMinC;
        @JsonProperty("temp_max_c") public double tempMaxC;
        @JsonProperty("temp_avg_c") public double tempAvgC;
        @JsonProperty("window_start") public long windowStart;
        @JsonProperty("window_end") public long windowEnd;
        @JsonProperty("reading_count") public int readingCount;
        public int reputation;
        @JsonProperty("timestamp_unix_secs") public long timestamp;

        public static Builder builder() { return new Builder(); }
        public static class Builder {
            private final TemperatureLogRequest r = new TemperatureLogRequest();
            public Builder batchId(String v) { r.batchId = v; return this; }
            public Builder sensorId(String v) { r.sensorId = v; return this; }
            public Builder location(String v) { r.location = v; return this; }
            public Builder tempMinC(double v) { r.tempMinC = v; return this; }
            public Builder tempMaxC(double v) { r.tempMaxC = v; return this; }
            public Builder tempAvgC(double v) { r.tempAvgC = v; return this; }
            public Builder windowStart(long v) { r.windowStart = v; return this; }
            public Builder windowEnd(long v) { r.windowEnd = v; return this; }
            public Builder readingCount(int v) { r.readingCount = v; return this; }
            public Builder reputation(int v) { r.reputation = v; return this; }
            public Builder timestamp(long v) { r.timestamp = v; return this; }
            public TemperatureLogRequest build() {
                if (r.timestamp == 0) r.timestamp = Instant.now().getEpochSecond();
                return r;
            }
        }
    }

    // --- HTTP methods ---

    private Receipt postEvent(Object request) throws IOException, InterruptedException {
        String body = mapper.writeValueAsString(request);
        HttpRequest req = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/events"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .timeout(Duration.ofSeconds(15))
            .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        return mapper.readValue(resp.body(), Receipt.class);
    }

    private <T> T getResource(String path, Class<T> type) throws IOException, InterruptedException {
        HttpRequest req = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + path))
            .GET()
            .timeout(Duration.ofSeconds(15))
            .build();
        HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
        return mapper.readValue(resp.body(), type);
    }

    // --- Event methods ---

    public Receipt batchCreated(BatchCreatedRequest r) throws IOException, InterruptedException {
        return postEvent(r);
    }

    public Receipt custodyTransfer(CustodyTransferRequest r) throws IOException, InterruptedException {
        return postEvent(r);
    }

    public Receipt customsCleared(CustomsClearedRequest r) throws IOException, InterruptedException {
        return postEvent(r);
    }

    public Receipt temperatureLog(TemperatureLogRequest r) throws IOException, InterruptedException {
        return postEvent(r);
    }

    public Receipt recallIssued(RecallIssuedRequest r) throws IOException, InterruptedException {
        return postEvent(r);
    }

    // --- Discovery ---

    public Health health() throws IOException, InterruptedException {
        return getResource("/health", Health.class);
    }
}
