package supply.escs;

import java.time.Instant;
import java.util.List;

/**
 * ESCS Java SDK — live integration tests
 * Run: mvn test  or  javac + java manually
 */
public class ESCSTest {

    static int passed = 0;
    static int failed = 0;

    static void test(String name, boolean condition) {
        if (condition) {
            System.out.println("  PASS: " + name);
            passed++;
        } else {
            System.out.println("  FAIL: " + name);
            failed++;
        }
    }

    public static void main(String[] args) throws Exception {
        ESCSClient client = new ESCSClient("http://127.0.0.1:7710");
        long now = Instant.now().getEpochSecond();

        System.out.println("=== ESCS Java SDK Tests ===\n");

        // Health
        ESCSClient.Health h = client.health();
        test("health ok", h.isOk());
        test("health service is adapterd", "adapterd".equals(h.getService()));
        test("health node_id present", h.getNodeId() != null && h.getNodeId().startsWith("ed25519:"));

        // Batch created
        ESCSClient.Receipt r = client.batchCreated(
            ESCSClient.BatchCreatedRequest.builder()
                .batchId("batch:JAVA-TEST-001")
                .productCode("DRUG-001")
                .quantity(5000)
                .unit("units")
                .originLocation("Chicago, IL")
                .producerId("party:producer")
                .lotNumber("LOT-JAVA-001")
                .manufactureDate(now)
                .expiryDate(now + 31536000L)
                .build()
        );
        test("batch_created ok", r.isOk());
        test("batch_created published", r.isPublished());
        test("batch_created witnessed", r.isWitnessed());
        test("batch_created digest starts sha256:", r.getDigest() != null && r.getDigest().startsWith("sha256:"));
        test("batch_created claim_space is SUPPLY.BATCH.v1", "SUPPLY.BATCH.v1".equals(r.getClaimSpace()));

        // Custody transfer
        r = client.custodyTransfer(
            ESCSClient.CustodyTransferRequest.builder()
                .batchId("batch:JAVA-TEST-001")
                .from("party:producer")
                .to("party:shipper")
                .location("Chicago, IL")
                .quantity(5000)
                .unit("units")
                .handoffMethod("truck")
                .build()
        );
        test("custody_transfer ok", r.isOk());
        test("custody_transfer published", r.isPublished());
        test("custody_transfer claim_space", "SUPPLY.CUSTODY.v1".equals(r.getClaimSpace()));

        // Customs cleared — rep=10 passes
        r = client.customsCleared(
            ESCSClient.CustomsClearedRequest.builder()
                .batchId("batch:JAVA-TEST-001")
                .customsAuthority("CBP")
                .clearanceRef("CBP-JAVA-001")
                .portOfEntry("JFK")
                .destinationCountry("US")
                .reputation(10)
                .build()
        );
        test("customs_cleared ok", r.isOk());
        test("customs_cleared published", r.isPublished());

        // Customs cleared — rep=9 denied
        r = client.customsCleared(
            ESCSClient.CustomsClearedRequest.builder()
                .batchId("batch:JAVA-TEST-001")
                .customsAuthority("CBP")
                .clearanceRef("CBP-JAVA-002")
                .portOfEntry("JFK")
                .destinationCountry("US")
                .reputation(9)
                .build()
        );
        test("customs gate denied at rep=9", !r.isPublished());

        // Temperature log
        r = client.temperatureLog(
            ESCSClient.TemperatureLogRequest.builder()
                .batchId("batch:JAVA-TEST-001")
                .sensorId("sensor:cold-007")
                .location("Chicago Cold Storage")
                .tempMinC(2.1)
                .tempMaxC(7.8)
                .tempAvgC(4.5)
                .windowStart(now - 299)
                .windowEnd(now)
                .readingCount(60)
                .reputation(1)
                .timestamp(now)
                .build()
        );
        test("temperature_log ok", r.isOk());
        test("temperature_log published", r.isPublished());

        // Recall issued — rep=50 passes
        r = client.recallIssued(
            ESCSClient.RecallIssuedRequest.builder()
                .recallId("recall:JAVA-TEST-001")
                .affectedBatchIds(List.of("batch:JAVA-TEST-001"))
                .affectedLotNumbers(List.of("LOT-JAVA-001"))
                .productCode("DRUG-001")
                .severity("class_i")
                .reason("java sdk test")
                .issuerId("oracle:fda-001")
                .instructions("destroy")
                .regulatoryRef("FDA-JAVA-2025-001")
                .reputation(50)
                .build()
        );
        test("recall_issued ok", r.isOk());
        test("recall_issued published", r.isPublished());
        test("recall_issued witnessed", r.isWitnessed());

        // Recall gate denied — rep=49
        r = client.recallIssued(
            ESCSClient.RecallIssuedRequest.builder()
                .recallId("recall:JAVA-TEST-002")
                .affectedBatchIds(List.of("batch:JAVA-TEST-001"))
                .affectedLotNumbers(List.of("LOT-JAVA-001"))
                .productCode("DRUG-001")
                .severity("class_i")
                .reason("should be denied")
                .issuerId("oracle:fda-001")
                .instructions("destroy")
                .regulatoryRef("FDA-JAVA-2025-002")
                .reputation(49)
                .build()
        );
        test("recall gate denied at rep=49", !r.isPublished());

        // Receipt URL present
        r = client.custodyTransfer(
            ESCSClient.CustodyTransferRequest.builder()
                .batchId("batch:JAVA-TEST-001")
                .from("party:shipper")
                .to("party:distributor")
                .location("New York, NY")
                .quantity(5000)
                .unit("units")
                .build()
        );
        test("receipt_url present", r.getReceiptUrl() != null && r.getReceiptUrl().startsWith("http"));

        System.out.println("\n=========================");
        System.out.println("  total  " + passed + " passed  " + failed + " failed");
        System.out.println("=========================");
        if (failed > 0) System.exit(1);
    }
}
