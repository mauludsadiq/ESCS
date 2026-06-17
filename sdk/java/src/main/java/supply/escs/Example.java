package supply.escs;

import java.time.Instant;
import java.util.List;

/**
 * ESCS Java SDK — Quickstart Example
 * Run: javac -cp jackson-databind.jar Example.java ESCSClient.java && java Example
 */
public class Example {
    public static void main(String[] args) throws Exception {
        ESCSClient client = new ESCSClient("http://localhost:7710");
        long now = Instant.now().getEpochSecond();

        // Health check
        ESCSClient.Health health = client.health();
        System.out.println("Connected: " + health.getNodeId().substring(0, 20) + "...");

        // 1. Batch created
        ESCSClient.Receipt r = client.batchCreated(
            ESCSClient.BatchCreatedRequest.builder()
                .batchId("batch:JAVA-SDK-DEMO-001")
                .productCode("DRUG-INSULIN-001")
                .quantity(10000)
                .unit("units")
                .originLocation("Chicago Pharma Facility, IL")
                .producerId("party:producer-chicago")
                .lotNumber("LOT-JAVA-001")
                .manufactureDate(now)
                .expiryDate(now + 31536000L)
                .build()
        );
        System.out.println("\n1. Batch created: " + r);

        // 2. Custody transfer
        r = client.custodyTransfer(
            ESCSClient.CustodyTransferRequest.builder()
                .batchId("batch:JAVA-SDK-DEMO-001")
                .from("party:producer-chicago")
                .to("party:cold-storage")
                .location("Chicago, IL")
                .quantity(10000)
                .unit("units")
                .handoffMethod("refrigerated_truck")
                .build()
        );
        System.out.println("2. Custody transfer: " + r);

        // 3. Temperature log
        r = client.temperatureLog(
            ESCSClient.TemperatureLogRequest.builder()
                .batchId("batch:JAVA-SDK-DEMO-001")
                .sensorId("sensor:cold-007")
                .location("Chicago Cold Storage")
                .tempMinC(2.1)
                .tempMaxC(7.8)
                .tempAvgC(4.5)
                .windowStart(now - 300)
                .windowEnd(now)
                .readingCount(60)
                .reputation(10)
                .build()
        );
        System.out.println("3. Temperature log: " + r);

        // 4. Customs cleared
        r = client.customsCleared(
            ESCSClient.CustomsClearedRequest.builder()
                .batchId("batch:JAVA-SDK-DEMO-001")
                .customsAuthority("CBP")
                .clearanceRef("CBP-2025-JAVA-001")
                .portOfEntry("JFK")
                .destinationCountry("US")
                .reputation(10)
                .build()
        );
        System.out.println("4. Customs cleared: " + r);

        // 5. Recall issued
        r = client.recallIssued(
            ESCSClient.RecallIssuedRequest.builder()
                .recallId("recall:JAVA-DEMO-001")
                .affectedBatchIds(List.of("batch:JAVA-SDK-DEMO-001"))
                .affectedLotNumbers(List.of("LOT-JAVA-001"))
                .productCode("DRUG-INSULIN-001")
                .severity("class_i")
                .reason("contamination detected")
                .issuerId("oracle:fda-001")
                .instructions("destroy immediately")
                .regulatoryRef("FDA-JAVA-2025-001")
                .reputation(50)
                .build()
        );
        System.out.println("5. Recall issued: " + r);
        System.out.println("\nAll receipts on Anka mesh: http://localhost:18080");
    }
}
