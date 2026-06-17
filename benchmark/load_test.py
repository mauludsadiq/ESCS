#!/usr/bin/env python3
"""
ESCS Load Test + Benchmark
Measures throughput and latency of the ESCS adapter and Anka mesh.

Usage:
    python3 benchmark/load_test.py
    python3 benchmark/load_test.py --events 1000 --workers 10
    python3 benchmark/load_test.py --mode offline  # signing only, no adapter
"""

import sys
import os
import time
import json
import argparse
import statistics
import threading
import queue
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk', 'python'))

import requests
from escs_offline import OfflineSigner, _canonical_json, _sha256

ADAPTER_URL = "http://localhost:7710"
ANKA_URL    = "http://localhost:18080"

# --- Result types ---

@dataclass
class EventResult:
    event_type: str
    latency_ms: float
    ok: bool
    published: bool
    witnessed: bool
    error: Optional[str] = None

@dataclass
class BenchmarkRun:
    label: str
    total_events: int
    workers: int
    duration_secs: float
    results: List[EventResult] = field(default_factory=list)

    @property
    def successful(self): return [r for r in self.results if r.ok]
    @property
    def failed(self): return [r for r in self.results if not r.ok]
    @property
    def published(self): return [r for r in self.results if r.published]
    @property
    def witnessed(self): return [r for r in self.results if r.witnessed]

    @property
    def throughput(self):
        return len(self.results) / self.duration_secs if self.duration_secs > 0 else 0

    def latencies(self):
        return [r.latency_ms for r in self.successful]

    def p(self, percentile):
        lats = sorted(self.latencies())
        if not lats: return 0
        idx = int(len(lats) * percentile / 100)
        return lats[min(idx, len(lats)-1)]

    def summary(self):
        lats = self.latencies()
        return {
            'label':          self.label,
            'total':          self.total_events,
            'workers':        self.workers,
            'duration_secs':  round(self.duration_secs, 2),
            'throughput_eps': round(self.throughput, 1),
            'success':        len(self.successful),
            'failed':         len(self.failed),
            'published':      len(self.published),
            'witnessed':      len(self.witnessed),
            'latency_ms': {
                'min':  round(min(lats), 1) if lats else 0,
                'p50':  round(self.p(50), 1),
                'p95':  round(self.p(95), 1),
                'p99':  round(self.p(99), 1),
                'max':  round(max(lats), 1) if lats else 0,
                'mean': round(statistics.mean(lats), 1) if lats else 0,
            }
        }

# --- Event generators ---

def make_custody_event(i):
    return {
        "event_type": "custody_transfer",
        "batch_id":   f"batch:LOAD-TEST-{i:06d}",
        "from":       "party:producer",
        "to":         "party:shipper",
        "location":   "Chicago, IL",
        "quantity":   100,
        "unit":       "units",
        "timestamp_unix_secs": int(time.time()),
    }

def make_batch_event(i):
    now = int(time.time())
    return {
        "event_type":      "batch_created",
        "batch_id":        f"batch:LOAD-TEST-{i:06d}",
        "product_code":    "DRUG-001",
        "quantity":        1000,
        "unit":            "units",
        "origin_location": "Chicago, IL",
        "producer_id":     "party:producer",
        "lot_number":      f"LOT-{i:06d}",
        "manufacture_date": now,
        "expiry_date":      now + 31536000,
        "timestamp_unix_secs": now,
    }

def make_sensor_event(i):
    now = int(time.time())
    return {
        "event_type":   "temperature_log",
        "batch_id":     f"batch:LOAD-TEST-{i:06d}",
        "sensor_id":    "sensor:load-test-001",
        "location":     "Chicago Cold Storage",
        "temp_min_c":   2.1,
        "temp_max_c":   7.8,
        "temp_avg_c":   4.5,
        "window_start": now - 299,
        "window_end":   now,
        "reading_count": 60,
        "reputation":   1,
        "timestamp_unix_secs": now,
    }

def make_inspection_event(i):
    return {
        "event_type":     "inspection_passed",
        "batch_id":       f"batch:LOAD-TEST-{i:06d}",
        "inspector_id":   "inspector:load-001",
        "inspection_type": "fda_gmp",
        "location":       "Chicago, IL",
        "standards":      ["FDA-21CFR"],
        "notes":          "load test",
        "reputation":     5,
        "timestamp_unix_secs": int(time.time()),
    }

EVENT_GENERATORS = {
    "custody_transfer": make_custody_event,
    "batch_created":    make_batch_event,
    "temperature_log":  make_sensor_event,
    "inspection_passed": make_inspection_event,
}

# --- HTTP worker ---

def publish_event(event):
    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{ADAPTER_URL}/events",
            json=event,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        data = resp.json()
        latency_ms = (time.perf_counter() - start) * 1000
        return EventResult(
            event_type=event.get("event_type", ""),
            latency_ms=latency_ms,
            ok=data.get("ok", False),
            published=data.get("published", False),
            witnessed=data.get("witnessed", False),
            error=data.get("reason") if not data.get("ok") else None
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return EventResult(
            event_type=event.get("event_type", ""),
            latency_ms=latency_ms,
            ok=False, published=False, witnessed=False,
            error=str(e)
        )

# --- Offline signing benchmark ---

def bench_offline_signing(n=1000, seed="bench-signer"):
    signer = OfflineSigner.generate(seed)
    event = make_custody_event(0)
    latencies = []

    start = time.perf_counter()
    for i in range(n):
        t0 = time.perf_counter()
        signer.sign_event(event)
        latencies.append((time.perf_counter() - t0) * 1000)
    duration = time.perf_counter() - start

    return {
        'label':         'offline_signing',
        'total':         n,
        'duration_secs': round(duration, 3),
        'throughput_eps': round(n / duration, 1),
        'latency_ms': {
            'min':  round(min(latencies), 3),
            'p50':  round(sorted(latencies)[n//2], 3),
            'p99':  round(sorted(latencies)[int(n*0.99)], 3),
            'max':  round(max(latencies), 3),
            'mean': round(sum(latencies)/len(latencies), 3),
        }
    }

# --- Throughput benchmark ---

def bench_throughput(event_type="custody_transfer", n=100, workers=5):
    gen = EVENT_GENERATORS.get(event_type, make_custody_event)
    events = [gen(i) for i in range(n)]
    results = []

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(publish_event, e) for e in events]
        for f in as_completed(futures):
            results.append(f.result())
    duration = time.perf_counter() - start

    run = BenchmarkRun(
        label=f"throughput_{event_type}",
        total_events=n,
        workers=workers,
        duration_secs=duration,
        results=results,
    )
    return run.summary()

# --- Scale benchmark: measure latency as mesh grows ---

def bench_scale(max_events=500, step=100, workers=5):
    results = []
    gen = make_custody_event
    total = 0

    for target in range(step, max_events + 1, step):
        batch_size = step
        batch = [gen(total + i) for i in range(batch_size)]
        batch_results = []

        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(publish_event, e) for e in batch]
            for f in as_completed(futures):
                batch_results.append(f.result())
        duration = time.perf_counter() - start

        total += batch_size
        lats = sorted([r.latency_ms for r in batch_results if r.ok])
        results.append({
            'claim_count':    total,
            'batch_size':     batch_size,
            'duration_secs':  round(duration, 2),
            'throughput_eps': round(batch_size / duration, 1),
            'p50_ms':  round(lats[len(lats)//2], 1) if lats else 0,
            'p95_ms':  round(lats[int(len(lats)*0.95)], 1) if lats else 0,
            'success': len([r for r in batch_results if r.ok]),
        })
        print(f"  {total:5d} claims | {round(batch_size/duration,1):6.1f} eps | "
              f"p50={round(lats[len(lats)//2],0) if lats else 'N/A':6}ms | "
              f"p95={round(lats[int(len(lats)*0.95)],0) if lats else 'N/A':6}ms")

    return results

# --- Gate overhead benchmark ---

def bench_gate_overhead():
    event_types = [
        ("custody_transfer",  make_custody_event,    0),
        ("batch_created",     make_batch_event,      0),
        ("inspection_passed", make_inspection_event, 5),
        ("temperature_log",   make_sensor_event,     1),
    ]
    results = []
    for name, gen, rep in event_types:
        event = gen(0)
        if rep > 0:
            event["reputation"] = rep
        latencies = []
        for _ in range(20):
            r = publish_event(event)
            if r.ok:
                latencies.append(r.latency_ms)
        if latencies:
            results.append({
                'event_type': name,
                'samples':    len(latencies),
                'mean_ms':    round(statistics.mean(latencies), 1),
                'p50_ms':     round(sorted(latencies)[len(latencies)//2], 1),
                'p99_ms':     round(sorted(latencies)[int(len(latencies)*0.99)], 1),
            })
    return results

# --- Anka mesh health ---

def mesh_health():
    try:
        r = requests.get(f"{ANKA_URL}/health", timeout=5)
        d = r.json()
        return {
            'ok':           d.get('ok', False),
            'claim_count':  d.get('claim_count', 0),
            'witness_count': d.get('witness_count', 0),
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description='ESCS Load Test')
    parser.add_argument('--events', type=int, default=200, help='Total events for throughput test')
    parser.add_argument('--workers', type=int, default=5, help='Concurrent workers')
    parser.add_argument('--scale-max', type=int, default=300, help='Max claims for scale test')
    parser.add_argument('--scale-step', type=int, default=100, help='Scale test step size')
    parser.add_argument('--mode', choices=['full', 'offline', 'throughput', 'scale', 'gate'],
                        default='full', help='Benchmark mode')
    parser.add_argument('--out', type=str, default='benchmark/results.json', help='Output file')
    args = parser.parse_args()

    report = {
        'timestamp': int(time.time()),
        'adapter_url': ADAPTER_URL,
        'anka_url': ANKA_URL,
        'config': {
            'events': args.events,
            'workers': args.workers,
            'scale_max': args.scale_max,
        }
    }

    print('=== ESCS Load Test + Benchmark ===\n')

    # Mesh health before
    print('Anka mesh health (before):')
    health_before = mesh_health()
    print(f"  claims: {health_before.get('claim_count', '?')}  "
          f"witnesses: {health_before.get('witness_count', '?')}\n")
    report['mesh_before'] = health_before

    # 1. Offline signing throughput
    if args.mode in ('full', 'offline'):
        print('1. Offline signing throughput (1,000 events, no adapter):')
        offline = bench_offline_signing(1000)
        print(f"   {offline['throughput_eps']} signs/sec  "
              f"p50={offline['latency_ms']['p50']}ms  "
              f"p99={offline['latency_ms']['p99']}ms\n")
        report['offline_signing'] = offline

    # 2. Throughput per event type
    if args.mode in ('full', 'throughput'):
        print(f'2. Adapter throughput ({args.events} events, {args.workers} workers):')
        report['throughput'] = {}
        for evt_type in ['custody_transfer', 'batch_created', 'temperature_log']:
            print(f'   {evt_type}...')
            result = bench_throughput(evt_type, args.events, args.workers)
            report['throughput'][evt_type] = result
            print(f"   -> {result['throughput_eps']} eps | "
                  f"p50={result['latency_ms']['p50']}ms | "
                  f"p95={result['latency_ms']['p95']}ms | "
                  f"p99={result['latency_ms']['p99']}ms | "
                  f"success={result['success']}/{result['total']}\n")

    # 3. Scale test
    if args.mode in ('full', 'scale'):
        print(f'3. Scale test (0 -> {args.scale_max} claims, step={args.scale_step}):')
        print(f'   {"claims":>7} | {"eps":>6} | {"p50":>8} | {"p95":>8} | success')
        scale = bench_scale(args.scale_max, args.scale_step, args.workers)
        report['scale'] = scale
        print()

    # 4. Gate overhead
    if args.mode in ('full', 'gate'):
        print('4. Gate policy overhead (20 samples per event type):')
        gate = bench_gate_overhead()
        report['gate_overhead'] = gate
        for g in gate:
            print(f"   {g['event_type']:25s}  mean={g['mean_ms']:6.1f}ms  "
                  f"p50={g['p50_ms']:6.1f}ms  p99={g['p99_ms']:6.1f}ms")
        print()

    # Mesh health after
    print('Anka mesh health (after):')
    health_after = mesh_health()
    print(f"  claims: {health_after.get('claim_count', '?')}  "
          f"witnesses: {health_after.get('witness_count', '?')}\n")
    report['mesh_after'] = health_after

    # Write results
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w') as f:
        json.dump(report, f, indent=2)
    print(f'Results written to {args.out}')

    # Summary
    print('\n=== Summary ===')
    if 'offline_signing' in report:
        o = report['offline_signing']
        print(f"Offline signing:    {o['throughput_eps']:>8.1f} signs/sec")
    if 'throughput' in report:
        for k, v in report['throughput'].items():
            print(f"{k:25s} {v['throughput_eps']:>8.1f} eps  "
                  f"p50={v['latency_ms']['p50']}ms  p99={v['latency_ms']['p99']}ms")

if __name__ == '__main__':
    main()
