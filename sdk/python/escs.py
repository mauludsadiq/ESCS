"""
ESCS Python SDK
Thin wrapper around the ESCS adapter HTTP API.

Install: pip install requests
Usage:
    from escs import ESCSClient
    client = ESCSClient("http://localhost:7710")
    receipt = client.custody_transfer(
        batch_id="batch:LOT-001",
        from_party="party:producer",
        to_party="party:shipper",
        location="Chicago, IL",
        quantity=1000,
        unit="units"
    )
    print(receipt.digest)
    print(receipt.receipt_url)
"""

import requests
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class Receipt:
    ok: bool
    published: bool
    witnessed: bool
    event_type: str
    batch_id: str
    claim_space: str
    digest: str
    issuer_node_id: str
    timestamp_unix_secs: int
    receipt_url: str
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "Receipt":
        return cls(
            ok=d.get("ok", False),
            published=d.get("published", False),
            witnessed=d.get("witnessed", False),
            event_type=d.get("event_type", ""),
            batch_id=d.get("batch_id", ""),
            claim_space=d.get("claim_space", ""),
            digest=d.get("digest", ""),
            issuer_node_id=d.get("issuer_node_id", ""),
            timestamp_unix_secs=d.get("timestamp_unix_secs", 0),
            receipt_url=d.get("receipt_url", ""),
            error=d.get("reason") or d.get("err"),
        )

    def __repr__(self):
        if self.ok:
            return f"Receipt(ok=True, digest={self.digest[:20]}..., witnessed={self.witnessed})"
        return f"Receipt(ok=False, error={self.error})"


@dataclass
class Provenance:
    batch_id: str
    chain_length: int
    current_holder: str
    under_recall: bool
    recall_count: int
    total_witnesses: int
    total_challenges: int
    contested: bool
    chain_integrity: bool
    chain: List[Dict]
    recalls: List[Dict]

    @classmethod
    def from_dict(cls, d: dict) -> "Provenance":
        return cls(
            batch_id=d.get("batch_id", ""),
            chain_length=d.get("chain_length", 0),
            current_holder=d.get("current_holder", ""),
            under_recall=d.get("under_recall", False),
            recall_count=d.get("recall_count", 0),
            total_witnesses=d.get("total_witnesses", 0),
            total_challenges=d.get("total_challenges", 0),
            contested=d.get("contested", False),
            chain_integrity=d.get("chain_integrity", True),
            chain=d.get("chain", []),
            recalls=d.get("recalls", []),
        )

    def __repr__(self):
        return (
            f"Provenance(batch_id={self.batch_id}, "
            f"chain_length={self.chain_length}, "
            f"current_holder={self.current_holder}, "
            f"under_recall={self.under_recall})"
        )


class ESCSError(Exception):
    pass


class ESCSClient:
    """
    ESCS Python SDK client.

    All methods return Receipt objects with ok, digest, receipt_url, etc.
    Provenance methods return Provenance objects.

    Example:
        client = ESCSClient("http://localhost:7710")
        r = client.custody_transfer("batch:001", "party:a", "party:b", "Chicago", 1000, "units")
        print(r.digest)
    """

    def __init__(self, base_url: str = "http://localhost:7710", timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _post(self, path: str, body: dict) -> dict:
        try:
            resp = self._session.post(
                f"{self.base_url}{path}", json=body, timeout=self.timeout
            )
            return resp.json()
        except requests.RequestException as e:
            raise ESCSError(f"Request failed: {e}")

    def _get(self, path: str) -> dict:
        try:
            resp = self._session.get(
                f"{self.base_url}{path}", timeout=self.timeout
            )
            return resp.json()
        except requests.RequestException as e:
            raise ESCSError(f"Request failed: {e}")

    def _now(self) -> int:
        return int(time.time())

    def _receipt(self, body: dict) -> Receipt:
        result = self._post("/events", body)
        return Receipt.from_dict(result)

    # --- Batch lifecycle ---

    def batch_created(
        self,
        batch_id: str,
        product_code: str,
        quantity: int,
        unit: str,
        origin_location: str,
        producer_id: str,
        lot_number: str,
        manufacture_date: int,
        expiry_date: int,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "batch_created",
            "batch_id": batch_id,
            "product_code": product_code,
            "quantity": quantity,
            "unit": unit,
            "origin_location": origin_location,
            "producer_id": producer_id,
            "lot_number": lot_number,
            "manufacture_date": manufacture_date,
            "expiry_date": expiry_date,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Custody ---

    def custody_transfer(
        self,
        batch_id: str,
        from_party: str,
        to_party: str,
        location: str,
        quantity: int,
        unit: str,
        handoff_method: str = "standard",
        actor_id: str = "",
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "custody_transfer",
            "batch_id": batch_id,
            "from": from_party,
            "to": to_party,
            "location": location,
            "quantity": quantity,
            "unit": unit,
            "handoff_method": handoff_method,
            "actor_id": actor_id,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Inspection ---

    def inspection_passed(
        self,
        batch_id: str,
        inspector_id: str,
        inspection_type: str,
        location: str,
        standards: List[str] = None,
        notes: str = "",
        reputation: int = 5,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "inspection_passed",
            "batch_id": batch_id,
            "inspector_id": inspector_id,
            "inspection_type": inspection_type,
            "location": location,
            "standards": standards or [],
            "notes": notes,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def inspection_failed(
        self,
        batch_id: str,
        inspector_id: str,
        inspection_type: str,
        location: str,
        failure_codes: List[str] = None,
        evidence_refs: List[str] = None,
        reputation: int = 5,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "inspection_failed",
            "batch_id": batch_id,
            "inspector_id": inspector_id,
            "inspection_type": inspection_type,
            "location": location,
            "failure_codes": failure_codes or [],
            "evidence_refs": evidence_refs or [],
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Customs ---

    def customs_cleared(
        self,
        batch_id: str,
        customs_authority: str,
        clearance_ref: str,
        port_of_entry: str,
        destination_country: str,
        actor_id: str = "",
        reputation: int = 10,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "customs_cleared",
            "batch_id": batch_id,
            "customs_authority": customs_authority,
            "clearance_ref": clearance_ref,
            "port_of_entry": port_of_entry,
            "destination_country": destination_country,
            "actor_id": actor_id,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def customs_held(
        self,
        batch_id: str,
        customs_authority: str,
        hold_ref: str,
        port_of_entry: str,
        reason: str,
        evidence_refs: List[str] = None,
        reputation: int = 10,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "customs_held",
            "batch_id": batch_id,
            "customs_authority": customs_authority,
            "hold_ref": hold_ref,
            "port_of_entry": port_of_entry,
            "reason": reason,
            "evidence_refs": evidence_refs or [],
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Cold chain ---

    def temperature_log(
        self,
        batch_id: str,
        sensor_id: str,
        location: str,
        temp_min_c: float,
        temp_max_c: float,
        temp_avg_c: float,
        window_start: int,
        window_end: int,
        reading_count: int,
        reputation: int = 1,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "temperature_log",
            "batch_id": batch_id,
            "sensor_id": sensor_id,
            "location": location,
            "temp_min_c": temp_min_c,
            "temp_max_c": temp_max_c,
            "temp_avg_c": temp_avg_c,
            "window_start": window_start,
            "window_end": window_end,
            "reading_count": reading_count,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def temperature_breach(
        self,
        batch_id: str,
        sensor_id: str,
        location: str,
        temp_c: float,
        threshold_min_c: float,
        threshold_max_c: float,
        breach_timestamp: int,
        duration_secs: int,
        evidence_ref: str = "",
        reputation: int = 1,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "temperature_breach",
            "batch_id": batch_id,
            "sensor_id": sensor_id,
            "location": location,
            "temp_c": temp_c,
            "threshold_min_c": threshold_min_c,
            "threshold_max_c": threshold_max_c,
            "breach_timestamp": breach_timestamp,
            "duration_secs": duration_secs,
            "evidence_ref": evidence_ref,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Certification ---

    def certification_issued(
        self,
        batch_id: str,
        cert_type: str,
        certifier_id: str,
        cert_ref: str,
        valid_from: int,
        valid_until: int,
        scope: str = "",
        reputation: int = 20,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "certification_issued",
            "batch_id": batch_id,
            "cert_type": cert_type,
            "certifier_id": certifier_id,
            "cert_ref": cert_ref,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "scope": scope,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def certification_revoked(
        self,
        batch_id: str,
        cert_type: str,
        certifier_id: str,
        cert_ref: str,
        reason: str,
        evidence_refs: List[str] = None,
        reputation: int = 20,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "certification_revoked",
            "batch_id": batch_id,
            "cert_type": cert_type,
            "certifier_id": certifier_id,
            "cert_ref": cert_ref,
            "reason": reason,
            "evidence_refs": evidence_refs or [],
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Recall ---

    def recall_issued(
        self,
        recall_id: str,
        affected_batch_ids: List[str],
        affected_lot_numbers: List[str],
        product_code: str,
        severity: str,
        reason: str,
        issuer_id: str,
        instructions: str,
        regulatory_ref: str,
        reputation: int = 50,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "recall_issued",
            "recall_id": recall_id,
            "affected_batch_ids": affected_batch_ids,
            "affected_lot_numbers": affected_lot_numbers,
            "product_code": product_code,
            "severity": severity,
            "reason": reason,
            "issuer_id": issuer_id,
            "instructions": instructions,
            "regulatory_ref": regulatory_ref,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def recall_acknowledged(
        self,
        recall_id: str,
        batch_id: str,
        holder_id: str,
        quantity_held: int,
        location: str,
        action_plan: str,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "recall_acknowledged",
            "recall_id": recall_id,
            "batch_id": batch_id,
            "holder_id": holder_id,
            "quantity_held": quantity_held,
            "location": location,
            "action_plan": action_plan,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def recall_resolved(
        self,
        recall_id: str,
        batch_id: str,
        holder_id: str,
        resolution: str,
        quantity_destroyed: int,
        quantity_returned: int,
        evidence_refs: List[str] = None,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "recall_resolved",
            "recall_id": recall_id,
            "batch_id": batch_id,
            "holder_id": holder_id,
            "resolution": resolution,
            "quantity_destroyed": quantity_destroyed,
            "quantity_returned": quantity_returned,
            "evidence_refs": evidence_refs or [],
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Sensor ---

    def sensor_reading(
        self,
        batch_id: str,
        sensor_id: str,
        sensor_type: str,
        location: str,
        value: float,
        unit: str,
        threshold_min: float,
        threshold_max: float,
        in_range: bool = True,
        reputation: int = 1,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "sensor_reading",
            "batch_id": batch_id,
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "location": location,
            "value": value,
            "unit": unit,
            "threshold_min": threshold_min,
            "threshold_max": threshold_max,
            "in_range": in_range,
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    # --- Location + Origin ---

    def location_update(
        self,
        batch_id: str,
        actor_id: str,
        location: str,
        coordinates: Dict = None,
        facility_id: str = "",
        scan_method: str = "rfid",
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "location_update",
            "batch_id": batch_id,
            "actor_id": actor_id,
            "location": location,
            "coordinates": coordinates or {"lat": 0.0, "lng": 0.0},
            "facility_id": facility_id,
            "scan_method": scan_method,
            "timestamp_unix_secs": timestamp or self._now(),
        })

    def origin_attested(
        self,
        batch_id: str,
        certifier_id: str,
        country_of_origin: str,
        region: str = "",
        facility_id: str = "",
        standards: List[str] = None,
        evidence_refs: List[str] = None,
        reputation: int = 10,
        timestamp: Optional[int] = None,
    ) -> Receipt:
        return self._receipt({
            "event_type": "origin_attested",
            "batch_id": batch_id,
            "certifier_id": certifier_id,
            "country_of_origin": country_of_origin,
            "region": region,
            "facility_id": facility_id,
            "standards": standards or [],
            "evidence_refs": evidence_refs or [],
            "reputation": reputation,
            "timestamp_unix_secs": timestamp or self._now(),
        })


    def submit_signed(self, envelope) -> "Receipt":
        """
        Submit a pre-signed envelope to the adapter.
        The adapter skips signing and goes straight to gate + Anka publish.
        """
        result = self._post("/submit_signed", envelope.to_dict())
        return Receipt.from_dict(result)

    # --- Provenance queries ---

    def provenance(self, batch_id: str) -> Provenance:
        result = self._get(f"/provenance/{batch_id}")
        return Provenance.from_dict(result)

    def provenance_summary(self, batch_id: str) -> dict:
        return self._get(f"/provenance/{batch_id}/summary")

    def recalls(self, batch_id: str) -> dict:
        return self._get(f"/provenance/{batch_id}/recalls")

    def custody_chain(self, batch_id: str) -> dict:
        return self._get(f"/provenance/{batch_id}/custody")

    def breaches(self, batch_id: str) -> dict:
        return self._get(f"/provenance/{batch_id}/breaches")

    # --- Discovery ---

    def jurisdictions(self) -> List[str]:
        return self._get("/jurisdictions").get("jurisdictions", [])

    def event_types(self) -> List[str]:
        return self._get("/events/types").get("event_types", [])

    def health(self) -> dict:
        return self._get("/health")
