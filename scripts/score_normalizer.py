#!/usr/bin/env python3
import json
import sys
import hashlib
from datetime import datetime, timezone

def generate_canonical_id(record_type, external_id):
    prefix_map = {
        'ProblemReport': 'PRB',
        'ChangeRequest': 'CR',
        'RiskItem': 'RSK'
    }
    prefix = prefix_map.get(record_type, 'UNK')
    return f"{prefix}-SCORE-{external_id}"

def normalize_records(input_file):
    with open(input_file, 'r') as f:
        extracted_data = json.load(f)

    normalized = []

    for record in extracted_data:
        canonical_id = generate_canonical_id(record['type'], record['external_id'])

        # Create a stable string for hashing to generate a version hash
        stable_repr = json.dumps(record, sort_keys=True)
        content_hash = hashlib.sha256(stable_repr.encode('utf-8')).hexdigest()

        normalized_record = {
            'canonical_id': canonical_id,
            'version': 1,
            'content_hash': content_hash,
            'ingested_at': datetime.now(timezone.utc).isoformat(),
            'source_system': 'Eclipse S-Core v0.6.0',
            'data': record
        }

        normalized.append(normalized_record)

    return normalized

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: score_normalizer.py <extracted.json> <normalized.json>")
        sys.exit(1)

    normalized_data = normalize_records(sys.argv[1])

    with open(sys.argv[2], 'w') as f:
        json.dump(normalized_data, f, indent=2)

    print(f"Normalized {len(normalized_data)} canonical records.")
