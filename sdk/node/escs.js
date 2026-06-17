/**
 * ESCS Node.js SDK
 * Thin wrapper around the ESCS adapter HTTP API.
 *
 * Install: npm install node-fetch  (or use built-in fetch in Node 18+)
 *
 * Usage:
 *   const { ESCSClient } = require('./escs')
 *   const client = new ESCSClient('http://localhost:7710')
 *   const receipt = await client.custodyTransfer({
 *     batchId: 'batch:LOT-001',
 *     from: 'party:producer',
 *     to: 'party:shipper',
 *     location: 'Chicago, IL',
 *     quantity: 1000,
 *     unit: 'units',
 *   })
 *   console.log(receipt.digest)
 *   console.log(receipt.receiptUrl)
 */

'use strict'

const now = () => Math.floor(Date.now() / 1000)

class Receipt {
  constructor(data) {
    this.ok                 = data.ok ?? false
    this.published          = data.published ?? false
    this.witnessed          = data.witnessed ?? false
    this.eventType          = data.event_type ?? ''
    this.batchId            = data.batch_id ?? ''
    this.claimSpace         = data.claim_space ?? ''
    this.digest             = data.digest ?? ''
    this.issuerNodeId       = data.issuer_node_id ?? ''
    this.timestampUnixSecs  = data.timestamp_unix_secs ?? 0
    this.receiptUrl         = data.receipt_url ?? ''
    this.error              = data.reason ?? data.err ?? null
  }

  toString() {
    if (this.ok) {
      return `Receipt(ok=true, digest=${this.digest.slice(0, 20)}..., witnessed=${this.witnessed})`
    }
    return `Receipt(ok=false, error=${this.error})`
  }
}

class Provenance {
  constructor(data) {
    this.batchId          = data.batch_id ?? ''
    this.chainLength      = data.chain_length ?? 0
    this.currentHolder    = data.current_holder ?? ''
    this.underRecall      = data.under_recall ?? false
    this.recallCount      = data.recall_count ?? 0
    this.totalWitnesses   = data.total_witnesses ?? 0
    this.totalChallenges  = data.total_challenges ?? 0
    this.contested        = data.contested ?? false
    this.chainIntegrity   = data.chain_integrity ?? true
    this.chain            = data.chain ?? []
    this.recalls          = data.recalls ?? []
  }

  toString() {
    return `Provenance(batchId=${this.batchId}, chainLength=${this.chainLength}, currentHolder=${this.currentHolder}, underRecall=${this.underRecall})`
  }
}

class ESCSError extends Error {
  constructor(message) {
    super(message)
    this.name = 'ESCSError'
  }
}

class ESCSClient {
  /**
   * @param {string} baseUrl - ESCS adapter URL (default: http://localhost:7710)
   * @param {object} options - { timeout: 10000 }
   */
  constructor(baseUrl = 'http://localhost:7710', options = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
    this.timeout = options.timeout ?? 10000
  }

  async _fetch(method, path, body = null) {
    const url = `${this.baseUrl}${path}`
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout ? AbortSignal.timeout(this.timeout) : undefined,
    }
    if (body) opts.body = JSON.stringify(body)

    let resp
    try {
      resp = await fetch(url, opts)
    } catch (e) {
      throw new ESCSError(`Request failed: ${e.message}`)
    }
    return resp.json()
  }

  async _post(path, body) {
    return this._fetch('POST', path, body)
  }

  async _get(path) {
    return this._fetch('GET', path)
  }

  async _receipt(body) {
    const data = await this._post('/events', body)
    return new Receipt(data)
  }

  // --- Batch lifecycle ---

  async batchCreated({
    batchId, productCode, quantity, unit,
    originLocation, producerId, lotNumber,
    manufactureDate, expiryDate, timestamp,
  }) {
    return this._receipt({
      event_type: 'batch_created',
      batch_id: batchId,
      product_code: productCode,
      quantity,
      unit,
      origin_location: originLocation,
      producer_id: producerId,
      lot_number: lotNumber,
      manufacture_date: manufactureDate,
      expiry_date: expiryDate,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Custody ---

  async custodyTransfer({
    batchId, from, to, location, quantity, unit,
    handoffMethod = 'standard', actorId = '', timestamp,
  }) {
    return this._receipt({
      event_type: 'custody_transfer',
      batch_id: batchId,
      from,
      to,
      location,
      quantity,
      unit,
      handoff_method: handoffMethod,
      actor_id: actorId,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Inspection ---

  async inspectionPassed({
    batchId, inspectorId, inspectionType, location,
    standards = [], notes = '', reputation = 5, timestamp,
  }) {
    return this._receipt({
      event_type: 'inspection_passed',
      batch_id: batchId,
      inspector_id: inspectorId,
      inspection_type: inspectionType,
      location,
      standards,
      notes,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async inspectionFailed({
    batchId, inspectorId, inspectionType, location,
    failureCodes = [], evidenceRefs = [], reputation = 5, timestamp,
  }) {
    return this._receipt({
      event_type: 'inspection_failed',
      batch_id: batchId,
      inspector_id: inspectorId,
      inspection_type: inspectionType,
      location,
      failure_codes: failureCodes,
      evidence_refs: evidenceRefs,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Customs ---

  async customsCleared({
    batchId, customsAuthority, clearanceRef,
    portOfEntry, destinationCountry, actorId = '',
    reputation = 10, timestamp,
  }) {
    return this._receipt({
      event_type: 'customs_cleared',
      batch_id: batchId,
      customs_authority: customsAuthority,
      clearance_ref: clearanceRef,
      port_of_entry: portOfEntry,
      destination_country: destinationCountry,
      actor_id: actorId,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async customsHeld({
    batchId, customsAuthority, holdRef, portOfEntry,
    reason, evidenceRefs = [], reputation = 10, timestamp,
  }) {
    return this._receipt({
      event_type: 'customs_held',
      batch_id: batchId,
      customs_authority: customsAuthority,
      hold_ref: holdRef,
      port_of_entry: portOfEntry,
      reason,
      evidence_refs: evidenceRefs,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Cold chain ---

  async temperatureLog({
    batchId, sensorId, location,
    tempMinC, tempMaxC, tempAvgC,
    windowStart, windowEnd, readingCount,
    reputation = 1, timestamp,
  }) {
    return this._receipt({
      event_type: 'temperature_log',
      batch_id: batchId,
      sensor_id: sensorId,
      location,
      temp_min_c: tempMinC,
      temp_max_c: tempMaxC,
      temp_avg_c: tempAvgC,
      window_start: windowStart,
      window_end: windowEnd,
      reading_count: readingCount,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async temperatureBreach({
    batchId, sensorId, location, tempC,
    thresholdMinC, thresholdMaxC, breachTimestamp,
    durationSecs, evidenceRef = '', reputation = 1, timestamp,
  }) {
    return this._receipt({
      event_type: 'temperature_breach',
      batch_id: batchId,
      sensor_id: sensorId,
      location,
      temp_c: tempC,
      threshold_min_c: thresholdMinC,
      threshold_max_c: thresholdMaxC,
      breach_timestamp: breachTimestamp,
      duration_secs: durationSecs,
      evidence_ref: evidenceRef,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Certification ---

  async certificationIssued({
    batchId, certType, certifierId, certRef,
    validFrom, validUntil, scope = '',
    reputation = 20, timestamp,
  }) {
    return this._receipt({
      event_type: 'certification_issued',
      batch_id: batchId,
      cert_type: certType,
      certifier_id: certifierId,
      cert_ref: certRef,
      valid_from: validFrom,
      valid_until: validUntil,
      scope,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async certificationRevoked({
    batchId, certType, certifierId, certRef,
    reason, evidenceRefs = [], reputation = 20, timestamp,
  }) {
    return this._receipt({
      event_type: 'certification_revoked',
      batch_id: batchId,
      cert_type: certType,
      certifier_id: certifierId,
      cert_ref: certRef,
      reason,
      evidence_refs: evidenceRefs,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Recall ---

  async recallIssued({
    recallId, affectedBatchIds, affectedLotNumbers,
    productCode, severity, reason, issuerId,
    instructions, regulatoryRef, reputation = 50, timestamp,
  }) {
    return this._receipt({
      event_type: 'recall_issued',
      recall_id: recallId,
      affected_batch_ids: affectedBatchIds,
      affected_lot_numbers: affectedLotNumbers,
      product_code: productCode,
      severity,
      reason,
      issuer_id: issuerId,
      instructions,
      regulatory_ref: regulatoryRef,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async recallAcknowledged({
    recallId, batchId, holderId,
    quantityHeld, location, actionPlan, timestamp,
  }) {
    return this._receipt({
      event_type: 'recall_acknowledged',
      recall_id: recallId,
      batch_id: batchId,
      holder_id: holderId,
      quantity_held: quantityHeld,
      location,
      action_plan: actionPlan,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async recallResolved({
    recallId, batchId, holderId, resolution,
    quantityDestroyed, quantityReturned,
    evidenceRefs = [], timestamp,
  }) {
    return this._receipt({
      event_type: 'recall_resolved',
      recall_id: recallId,
      batch_id: batchId,
      holder_id: holderId,
      resolution,
      quantity_destroyed: quantityDestroyed,
      quantity_returned: quantityReturned,
      evidence_refs: evidenceRefs,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  // --- Sensor, Location, Origin ---

  async sensorReading({
    batchId, sensorId, sensorType, location,
    value, unit, thresholdMin, thresholdMax,
    inRange = true, reputation = 1, timestamp,
  }) {
    return this._receipt({
      event_type: 'sensor_reading',
      batch_id: batchId,
      sensor_id: sensorId,
      sensor_type: sensorType,
      location,
      value,
      unit,
      threshold_min: thresholdMin,
      threshold_max: thresholdMax,
      in_range: inRange,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async locationUpdate({
    batchId, actorId, location,
    coordinates = { lat: 0, lng: 0 },
    facilityId = '', scanMethod = 'rfid', timestamp,
  }) {
    return this._receipt({
      event_type: 'location_update',
      batch_id: batchId,
      actor_id: actorId,
      location,
      coordinates,
      facility_id: facilityId,
      scan_method: scanMethod,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }

  async originAttested({
    batchId, certifierId, countryOfOrigin,
    region = '', facilityId = '',
    standards = [], evidenceRefs = [],
    reputation = 10, timestamp,
  }) {
    return this._receipt({
      event_type: 'origin_attested',
      batch_id: batchId,
      certifier_id: certifierId,
      country_of_origin: countryOfOrigin,
      region,
      facility_id: facilityId,
      standards,
      evidence_refs: evidenceRefs,
      reputation,
      timestamp_unix_secs: timestamp ?? now(),
    })
  }


  async submitSigned(envelope) {
    const data = await this._post('/submit_signed', envelope.toDict())
    return new Receipt(data)
  }

  // --- Provenance queries ---

  async provenance(batchId) {
    const data = await this._get(`/provenance/${batchId}`)
    return new Provenance(data)
  }

  async provenanceSummary(batchId) {
    return this._get(`/provenance/${batchId}/summary`)
  }

  async recalls(batchId) {
    return this._get(`/provenance/${batchId}/recalls`)
  }

  async custodyChain(batchId) {
    return this._get(`/provenance/${batchId}/custody`)
  }

  async breaches(batchId) {
    return this._get(`/provenance/${batchId}/breaches`)
  }

  // --- Discovery ---

  async health() {
    return this._get('/health')
  }

  async jurisdictions() {
    const data = await this._get('/jurisdictions')
    return data.jurisdictions ?? []
  }

  async eventTypes() {
    const data = await this._get('/events/types')
    return data.event_types ?? []
  }
}

module.exports = { ESCSClient, Receipt, Provenance, ESCSError }
