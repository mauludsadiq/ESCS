/**
 * ESCS Node.js SDK — Quickstart Example
 * Pharmaceutical cold chain: batch creation through customs clearance.
 *
 * Run with: node example.js
 * Requires Node 18+ (built-in fetch) or: npm install node-fetch
 */

const { ESCSClient } = require('./escs')

const client = new ESCSClient('http://localhost:7710')
const nowSecs = () => Math.floor(Date.now() / 1000)

async function main() {
  // Health check
  const health = await client.health()
  console.log(`Connected: node=${health.node_id.slice(0, 20)}...`)
  console.log(`Supported events: ${health.supported_events.length}`)

  // 1. Batch created
  let r = await client.batchCreated({
    batchId: 'batch:NODE-SDK-DEMO-001',
    productCode: 'DRUG-INSULIN-001',
    quantity: 10000,
    unit: 'units',
    originLocation: 'Chicago Pharma Facility, IL',
    producerId: 'party:producer-chicago',
    lotNumber: 'LOT-NODE-001',
    manufactureDate: 1710000000,
    expiryDate: 1741536000,
  })
  console.log(`\n1. Batch created: ${r}`)
  console.log(`   Receipt: ${r.receiptUrl}`)

  // 2. Custody transfer
  r = await client.custodyTransfer({
    batchId: 'batch:NODE-SDK-DEMO-001',
    from: 'party:producer-chicago',
    to: 'party:cold-storage',
    location: 'Chicago, IL',
    quantity: 10000,
    unit: 'units',
    handoffMethod: 'refrigerated_truck',
  })
  console.log(`\n2. Custody transfer: ${r}`)

  // 3. Temperature log (current window)
  const windowEnd = nowSecs()
  const windowStart = windowEnd - 300
  r = await client.temperatureLog({
    batchId: 'batch:NODE-SDK-DEMO-001',
    sensorId: 'sensor:cold-007',
    location: 'Chicago Cold Storage',
    tempMinC: 2.1,
    tempMaxC: 7.8,
    tempAvgC: 4.5,
    windowStart,
    windowEnd,
    readingCount: 60,
    reputation: 10,
  })
  console.log(`\n3. Temperature log: ${r}`)

  // 4. Inspection passed
  r = await client.inspectionPassed({
    batchId: 'batch:NODE-SDK-DEMO-001',
    inspectorId: 'inspector:fda-001',
    inspectionType: 'fda_gmp',
    location: 'Chicago Cold Storage',
    standards: ['FDA-21CFR-211'],
    notes: 'all units verified',
    reputation: 5,
  })
  console.log(`\n4. Inspection: ${r}`)

  // 5. Customs cleared
  r = await client.customsCleared({
    batchId: 'batch:NODE-SDK-DEMO-001',
    customsAuthority: 'CBP',
    clearanceRef: 'CBP-2025-NODE-001',
    portOfEntry: 'JFK',
    destinationCountry: 'US',
    reputation: 10,
  })
  console.log(`\n5. Customs: ${r}`)

  // 6. Certification issued
  r = await client.certificationIssued({
    batchId: 'batch:NODE-SDK-DEMO-001',
    certType: 'fda_gmp',
    certifierId: 'certifier:fda-001',
    certRef: 'FDA-GMP-2025-NODE-001',
    validFrom: nowSecs(),
    validUntil: nowSecs() + 31536000,
    scope: 'full batch',
    reputation: 20,
  })
  console.log(`\n6. Certification: ${r}`)

  console.log(`\nAll receipts on Anka mesh: http://localhost:18080`)
}

main().catch(console.error)
