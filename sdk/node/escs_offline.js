/**
 * ESCS Offline Signing — Node.js
 *
 * Sign supply chain events locally without the adapter running.
 * Requires Node 18+ (built-in crypto for Ed25519).
 *
 * Usage:
 *   const { OfflineSigner, OfflineQueue } = require('./escs_offline')
 *
 *   const signer = OfflineSigner.generate('my-institution-seed')
 *   const envelope = signer.signEvent({
 *     event_type: 'custody_transfer',
 *     batch_id: 'batch:LOT-001',
 *     from: 'party:producer',
 *     to: 'party:shipper',
 *     location: 'Chicago, IL',
 *     quantity: 1000,
 *     unit: 'units',
 *   })
 *   console.log(envelope.digest)   // sha256:...
 *   console.log(envelope.signed)   // true
 *
 *   // Submit when online
 *   const { ESCSClient } = require('./escs')
 *   const client = new ESCSClient('http://localhost:7710')
 *   const receipt = await client.submitSigned(envelope)
 *   console.log(receipt.published, receipt.witnessed)
 */

'use strict'

const crypto = require('crypto')
const fs = require('fs')
const path = require('path')

// --- Canonical JSON ---

function canonicalJson(obj) {
  if (obj === null) return 'null'
  if (typeof obj === 'boolean') return obj ? 'true' : 'false'
  if (typeof obj === 'number') return String(obj)
  if (typeof obj === 'string') return JSON.stringify(obj)
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalJson).join(',') + ']'
  }
  if (typeof obj === 'object') {
    const keys = Object.keys(obj).sort()
    return '{' + keys.map(k => `${JSON.stringify(k)}:${canonicalJson(obj[k])}`).join(',') + '}'
  }
  return JSON.stringify(obj)
}

// --- SHA-256 ---

function sha256(text) {
  return 'sha256:' + crypto.createHash('sha256').update(text, 'utf8').digest('hex')
}

// --- Claim space routing ---

const CLAIM_SPACE_MAP = {
  batch_created:         'SUPPLY.BATCH.v1',
  batch_split:           'SUPPLY.BATCH.v1',
  batch_merge:           'SUPPLY.BATCH.v1',
  custody_transfer:      'SUPPLY.CUSTODY.v1',
  inspection_passed:     'SUPPLY.INSPECTION.v1',
  inspection_failed:     'SUPPLY.INSPECTION.v1',
  customs_cleared:       'SUPPLY.CUSTOMS.US.v1',
  customs_held:          'SUPPLY.CUSTOMS.US.v1',
  temperature_log:       'SUPPLY.SENSOR.v1',
  temperature_breach:    'SUPPLY.SENSOR.v1',
  certification_issued:  'SUPPLY.ISO9001.v1',
  certification_revoked: 'SUPPLY.ISO9001.v1',
  recall_issued:         'SUPPLY.RECALL.v1',
  recall_acknowledged:   'SUPPLY.CUSTODY.v1',
  recall_resolved:       'SUPPLY.CUSTODY.v1',
  sensor_reading:        'SUPPLY.SENSOR.v1',
  location_update:       'SUPPLY.STATE.v1',
  origin_attested:       'SUPPLY.ORACLE.v1',
}

function mapEventToClaim(event, timestamp, issuerNodeId) {
  const kind = event.event_type || ''
  const batchId = event.batch_id || ''
  const claimSpace = CLAIM_SPACE_MAP[kind] || 'SUPPLY.STATE.v1'
  const subject = `sc:${kind}:${batchId}`
  const { event_type, ...rest } = event
  const objectJson = canonicalJson(rest)

  return {
    claim_space:         claimSpace,
    subject:             subject,
    predicate:           kind,
    object:              objectJson,
    evidence_refs:       [],
    issuer_node_id:      issuerNodeId,
    timestamp_unix_secs: timestamp,
  }
}

// --- SignedEnvelope ---

class SignedEnvelope {
  constructor({ claim, digest, issuerSignatureHex, issuerPublicKeyHex, eventType, batchId }) {
    this.claim = claim
    this.digest = digest
    this.issuerSignatureHex = issuerSignatureHex
    this.issuerPublicKeyHex = issuerPublicKeyHex
    this.eventType = eventType || ''
    this.batchId = batchId || ''
    this.signed = true
    this.published = false
    this.witnessed = false
  }

  toDict() {
    return {
      claim:                  this.claim,
      digest_hex:             this.digest,
      issuer_signature_hex:   this.issuerSignatureHex,
      issuer_public_key_hex:  this.issuerPublicKeyHex,
      event_type:             this.eventType,
      batch_id:               this.batchId,
    }
  }

  static fromDict(d) {
    return new SignedEnvelope({
      claim:               d.claim,
      digest:              d.digest_hex,
      issuerSignatureHex:  d.issuer_signature_hex,
      issuerPublicKeyHex:  d.issuer_public_key_hex,
      eventType:           d.event_type,
      batchId:             d.batch_id,
    })
  }

  toString() {
    return `SignedEnvelope(digest=${this.digest.slice(0, 22)}..., signed=${this.signed}, published=${this.published})`
  }
}

// --- OfflineSigner ---

class OfflineSigner {
  constructor(privateKeyHex, publicKeyHex, nodeId) {
    this._privateKeyHex = privateKeyHex
    this._publicKeyHex = publicKeyHex
    this._nodeId = nodeId
  }

  static generate(seed = '') {
    let privateKeyBytes
    if (seed) {
      privateKeyBytes = crypto.createHash('sha256').update(seed, 'utf8').digest()
    } else {
      privateKeyBytes = crypto.randomBytes(32)
    }

    const privateKey = crypto.createPrivateKey({
      key: Buffer.concat([
        Buffer.from('302e020100300506032b657004220420', 'hex'),
        privateKeyBytes
      ]),
      format: 'der',
      type: 'pkcs8',
    })

    const publicKey = crypto.createPublicKey(privateKey)
    const pubDer = publicKey.export({ format: 'der', type: 'spki' })
    const pubBytes = pubDer.slice(12) // strip SPKI header

    const privHex = privateKeyBytes.toString('hex')
    const pubHex = Buffer.from(pubBytes).toString('hex')
    const nodeId = `ed25519:${pubHex}`

    return new OfflineSigner(privHex, pubHex, nodeId)
  }

  static load(filePath) {
    const kp = JSON.parse(fs.readFileSync(filePath, 'utf8'))
    return new OfflineSigner(kp.private_key_hex, kp.public_key_hex, kp.node_id)
  }

  save(filePath) {
    fs.writeFileSync(filePath, JSON.stringify({
      private_key_hex: this._privateKeyHex,
      public_key_hex:  this._publicKeyHex,
      node_id:         this._nodeId,
    }, null, 2))
  }

  get nodeId() { return this._nodeId }
  get publicKeyHex() { return this._publicKeyHex }

  signEvent(event, timestamp = 0) {
    const ts = timestamp || Math.floor(Date.now() / 1000)
    const claim = mapEventToClaim(event, ts, this._nodeId)
    const canonical = canonicalJson(claim)
    const digest = sha256(canonical)
    const digestRaw = Buffer.from(digest.slice(7), 'hex')

    const privateKeyDer = Buffer.concat([
      Buffer.from('302e020100300506032b657004220420', 'hex'),
      Buffer.from(this._privateKeyHex, 'hex')
    ])
    const privateKey = crypto.createPrivateKey({
      key: privateKeyDer, format: 'der', type: 'pkcs8'
    })

    const sig = crypto.sign(null, digestRaw, privateKey)
    const sigHex = sig.toString('hex')

    return new SignedEnvelope({
      claim,
      digest,
      issuerSignatureHex: sigHex,
      issuerPublicKeyHex: this._publicKeyHex,
      eventType: event.event_type || '',
      batchId: event.batch_id || '',
    })
  }

  verify(envelope) {
    try {
      // Use THIS signer's public key, not the one in the envelope
      const pubKeyDer = Buffer.concat([
        Buffer.from('302a300506032b6570032100', 'hex'),
        Buffer.from(this._publicKeyHex, 'hex')
      ])
      const publicKey = crypto.createPublicKey({
        key: pubKeyDer, format: 'der', type: 'spki'
      })
      const digestRaw = Buffer.from(envelope.digest.slice(7), 'hex')
      const sig = Buffer.from(envelope.issuerSignatureHex, 'hex')
      return crypto.verify(null, digestRaw, publicKey, sig)
    } catch (e) {
      return false
    }
  }
}

// --- OfflineQueue ---

class OfflineQueue {
  constructor(filePath = 'escs_queue.jsonl') {
    this.filePath = filePath
    this._queue = []
    if (fs.existsSync(filePath)) {
      this._load()
    }
  }

  _load() {
    const lines = fs.readFileSync(this.filePath, 'utf8').split('\n').filter(Boolean)
    this._queue = lines.map(l => SignedEnvelope.fromDict(JSON.parse(l)))
  }

  _save() {
    const lines = this._queue.map(e => JSON.stringify(e.toDict()))
    fs.writeFileSync(this.filePath, lines.join('\n') + (lines.length ? '\n' : ''))
  }

  enqueue(envelope) {
    this._queue.push(envelope)
    this._save()
  }

  get length() { return this._queue.length }

  pending() {
    return this._queue.filter(e => !e.published)
  }

  async flush(client) {
    const results = []
    for (const env of this.pending()) {
      try {
        const receipt = await client.submitSigned(env)
        env.published = receipt.published
        env.witnessed = receipt.witnessed
        results.push(receipt)
      } catch (e) {
        results.push({ ok: false, err: e.message })
      }
    }
    this._save()
    return results
  }

  clear() {
    this._queue = []
    if (fs.existsSync(this.filePath)) fs.unlinkSync(this.filePath)
  }
}

module.exports = { OfflineSigner, OfflineQueue, SignedEnvelope, canonicalJson, sha256 }
