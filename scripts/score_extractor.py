#!/usr/bin/env python3
import json
import sys

def normalize_severity(severity):
    severity = severity.lower()
    if severity in ['critical', 'blocker', 'fatal']:
        return 'Critical'
    elif severity in ['high', 'major', 'error']:
        return 'High'
    elif severity in ['medium', 'normal', 'warning']:
        return 'Medium'
    else:
        return 'Low'

def extract_records(input_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    supported_classes = ['ProblemReport', 'ChangeRequest', 'RiskItem']
    extracted = []

    for record in data:
        artifact_class = record.get('Class')
        if artifact_class not in supported_classes:
            continue

        canonical_record = {
            'type': artifact_class,
            'external_id': record.get('ID'),
            'title': record.get('Title') or record.get('Summary'),
            'priority': normalize_severity(record.get('Severity', 'Low')),
            'reporter': record.get('Submitter'),
            'created_at': record.get('CreationDate'),
            'status': 'Intake-Pending' # By default, per 0019-03
        }

        extracted.append(canonical_record)

    return extracted

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: score_extractor.py <input.json> <output.json>")
        sys.exit(1)

    extracted_data = extract_records(sys.argv[1])

    with open(sys.argv[2], 'w') as f:
        json.dump(extracted_data, f, indent=2)

    print(f"Extracted {len(extracted_data)} records.")
