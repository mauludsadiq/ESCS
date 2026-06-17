"""
ESCS Offline Signing — Python

Allows institutions to sign supply chain claims locally without
the adapter running. Signed envelopes can be submitted later
when the adapter is available.

Usage:
    from escs_offline import OfflineSigner, OfflineQueue

    # Generate or load a keypair
    signer = OfflineSigner.generate("my-institution-seed")
    # or: signer = OfflineSigner.load("keypair.json")

    # Sign an event locally
    envelope = signer.sign_event({
        "event_type": "custody_transfer",
        "batch_id": "batch:LOT-001",
        "from": "party:producer",
        "to": "party:shipper",
        "location": "Chicago, IL",
        "quantity": 1000,
        "unit": "units",
    })
    print(envelope.digest)     # sha256:...
    print(envelope.signed)     # True — signed locally, not yet published

    # Submit when online
    from escs import ESCSClient
    client = ESCSClient("http://localhost:7710")
    receipt = client.submit_signed(envelope)
    print(receipt.published)   # True
    print(receipt.witnessed)   # True

    # Or use the queue for batch submission
    queue = OfflineQueue("queue.jsonl")
    queue.enqueue(envelope)
    results = queue.flush(client)
"""

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

# Ed25519 via cryptography library (pip install cryptography)
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, PrivateFormat, NoEncryption
    )
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def _require_crypto():
    if not HAS_CRYPTO:
        raise ImportError(
            "pip install cryptography  — required for offline signing"
        )


def _canonical_json(obj: Any) -> str:
    """Deterministic JSON — sorted keys, no whitespace."""
    if isinstance(obj, dict):
        return '{' + ','.join(
            f'"{k}":{_canonical_json(v)}'
            for k, v in sorted(obj.items())
        ) + '}'
    elif isinstance(obj, list):
        return '[' + ','.join(_canonical_json(v) for v in obj) + ']'
    elif isinstance(obj, bool):
        return 'true' if obj else 'false'
    elif obj is None:
        return 'null'
    elif isinstance(obj, (int, float)):
        return str(obj)
    else:
        return json.dumps(str(obj))


def _sha256(text: str) -> str:
    return 'sha256:' + hashlib.sha256(text.encode()).hexdigest()


def _map_event_to_claim(event: dict, timestamp: int, issuer_node_id: str) -> dict:
    """Convert an ESCS event dict to an eOS claim record."""
    kind = event.get('event_type', '')
    batch_id = event.get('batch_id', '')

    claim_space_map = {
        'batch_created':         'SUPPLY.BATCH.v1',
        'batch_split':           'SUPPLY.BATCH.v1',
        'batch_merge':           'SUPPLY.BATCH.v1',
        'custody_transfer':      'SUPPLY.CUSTODY.v1',
        'inspection_passed':     'SUPPLY.INSPECTION.v1',
        'inspection_failed':     'SUPPLY.INSPECTION.v1',
        'customs_cleared':       'SUPPLY.CUSTOMS.US.v1',
        'customs_held':          'SUPPLY.CUSTOMS.US.v1',
        'temperature_log':       'SUPPLY.SENSOR.v1',
        'temperature_breach':    'SUPPLY.SENSOR.v1',
        'certification_issued':  'SUPPLY.ISO9001.v1',
        'certification_revoked': 'SUPPLY.ISO9001.v1',
        'recall_issued':         'SUPPLY.RECALL.v1',
        'recall_acknowledged':   'SUPPLY.CUSTODY.v1',
        'recall_resolved':       'SUPPLY.CUSTODY.v1',
        'sensor_reading':        'SUPPLY.SENSOR.v1',
        'location_update':       'SUPPLY.STATE.v1',
        'origin_attested':       'SUPPLY.ORACLE.v1',
    }

    claim_space = claim_space_map.get(kind, 'SUPPLY.STATE.v1')
    subject = f'sc:{kind}:{batch_id}'
    object_json = _canonical_json({k: v for k, v in event.items() if k != 'event_type'})

    return {
        'claim_space':         claim_space,
        'subject':             subject,
        'predicate':           kind,
        'object':              object_json,
        'evidence_refs':       [],
        'issuer_node_id':      issuer_node_id,
        'timestamp_unix_secs': timestamp,
    }


@dataclass
class SignedEnvelope:
    claim: dict
    digest: str
    issuer_signature_hex: str
    issuer_public_key_hex: str
    signed: bool = True
    published: bool = False
    witnessed: bool = False
    event_type: str = ''
    batch_id: str = ''

    def to_dict(self) -> dict:
        # ensure claim is a dict not a string
        claim = self.claim if isinstance(self.claim, dict) else self.claim
        return {
            'claim':                claim,
            'digest_hex':           self.digest,
            'issuer_signature_hex': self.issuer_signature_hex,
            'issuer_public_key_hex': self.issuer_public_key_hex,
            'event_type':           self.event_type,
            'batch_id':             self.batch_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'SignedEnvelope':
        obj = cls(
            claim=d['claim'],
            digest=d['digest_hex'],
            issuer_signature_hex=d['issuer_signature_hex'],
            issuer_public_key_hex=d['issuer_public_key_hex'],
            event_type=d.get('event_type', ''),
            batch_id=d.get('batch_id', ''),
        )
        obj.issuerSignatureHex = d['issuer_signature_hex']
        return obj

    def __repr__(self):
        return f'SignedEnvelope(digest={self.digest[:22]}..., signed={self.signed}, published={self.published})'


class OfflineSigner:
    """
    Ed25519 signer for ESCS supply chain events.
    Replicates the EOS kernel signing logic in Python.
    """

    def __init__(self, private_key_hex: str, public_key_hex: str, node_id: str):
        _require_crypto()
        self._private_key_hex = private_key_hex
        self._public_key_hex = public_key_hex
        self._node_id = node_id
        self._private_key = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(private_key_hex)
        )

    @classmethod
    def generate(cls, seed: str = '') -> 'OfflineSigner':
        """Generate a new Ed25519 keypair from an optional seed string."""
        _require_crypto()
        if seed:
            seed_bytes = hashlib.sha256(seed.encode()).digest()
            private_key = Ed25519PrivateKey.from_private_bytes(seed_bytes)
        else:
            private_key = Ed25519PrivateKey.generate()

        public_key = private_key.public_key()
        pub_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
        priv_bytes = private_key.private_bytes(
            Encoding.Raw, PrivateFormat.Raw, NoEncryption()
        )

        pub_hex = pub_bytes.hex()
        priv_hex = priv_bytes.hex()
        node_id = f'ed25519:{pub_hex}'
        return cls(priv_hex, pub_hex, node_id)

    @classmethod
    def load(cls, path: str) -> 'OfflineSigner':
        """Load keypair from a JSON file."""
        with open(path) as f:
            kp = json.load(f)
        return cls(kp['private_key_hex'], kp['public_key_hex'], kp['node_id'])

    def save(self, path: str):
        """Save keypair to a JSON file."""
        with open(path, 'w') as f:
            json.dump({
                'private_key_hex': self._private_key_hex,
                'public_key_hex':  self._public_key_hex,
                'node_id':         self._node_id,
            }, f, indent=2)

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def public_key_hex(self) -> str:
        return self._public_key_hex

    def sign_event(self, event: dict, timestamp: int = 0,
                   reputation: int = 0) -> SignedEnvelope:
        """
        Sign an ESCS supply chain event locally.
        Returns a SignedEnvelope ready for submission.
        """
        ts = timestamp or int(time.time())
        claim = _map_event_to_claim(event, ts, self._node_id)

        # Canonical JSON of the claim
        canonical = _canonical_json(claim)

        # SHA-256 digest
        digest = _sha256(canonical)
        digest_raw = bytes.fromhex(digest[7:])  # strip 'sha256:'

        # Ed25519 signature over the raw digest bytes
        sig_bytes = self._private_key.sign(digest_raw)
        sig_hex = sig_bytes.hex()

        return SignedEnvelope(
            claim=claim,
            digest=digest,
            issuer_signature_hex=sig_hex,
            issuer_public_key_hex=self._public_key_hex,
            event_type=event.get('event_type', ''),
            batch_id=event.get('batch_id', ''),
        )

    def verify(self, envelope: SignedEnvelope) -> bool:
        """Verify a signed envelope was signed by THIS signer's private key."""
        _require_crypto()
        try:
            # Use THIS signer's public key, not the one in the envelope
            pub = Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(self._public_key_hex)
            )
            digest_raw = bytes.fromhex(envelope.digest[7:])
            sig_bytes = bytes.fromhex(envelope.issuer_signature_hex)
            pub.verify(sig_bytes, digest_raw)
            return True
        except Exception:
            return False

    @staticmethod
    def verify_envelope(envelope: SignedEnvelope) -> bool:
        """Verify a signed envelope using the public key embedded in the envelope."""
        _require_crypto()
        try:
            pub = Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(envelope.issuer_public_key_hex)
            )
            digest_raw = bytes.fromhex(envelope.digest[7:])
            sig_bytes = bytes.fromhex(envelope.issuer_signature_hex)
            pub.verify(sig_bytes, digest_raw)
            return True
        except Exception:
            return False


class OfflineQueue:
    """
    Local queue for signed envelopes pending submission.
    Persists to a JSONL file for durability across restarts.
    """

    def __init__(self, path: str = 'escs_queue.jsonl'):
        self.path = Path(path)
        self._queue: List[SignedEnvelope] = []
        if self.path.exists():
            self._load()

    def _load(self):
        self._queue = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    self._queue.append(SignedEnvelope.from_dict(json.loads(line)))

    def _save(self):
        with open(self.path, 'w') as f:
            for env in self._queue:
                f.write(json.dumps(env.to_dict()) + '\n')

    def enqueue(self, envelope: SignedEnvelope):
        """Add a signed envelope to the queue."""
        self._queue.append(envelope)
        self._save()

    def __len__(self):
        return len(self._queue)

    def pending(self) -> List[SignedEnvelope]:
        return [e for e in self._queue if not e.published]

    def flush(self, client) -> List:
        """
        Submit all pending envelopes to the adapter.
        Returns list of receipts.
        """
        results = []
        for env in self.pending():
            try:
                receipt = client.submit_signed(env)
                env.published = receipt.published
                env.witnessed = receipt.witnessed
                results.append(receipt)
            except Exception as e:
                results.append({'ok': False, 'err': str(e)})
        self._save()
        return results

    def clear(self):
        self._queue = []
        if self.path.exists():
            self.path.unlink()
