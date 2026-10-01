#!/usr/bin/env python3
"""Agent bootstrap boundary validator and client compatibility tool (Task 0037-42).

Provides deterministic protocol version negotiation, capability discovery,
and fail-closed validation for agent runtimes and client handshakes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PROTOCOL_VERSION_CURRENT = "2025-06-18"
SUPPORTED_PROTOCOLS = frozenset({"2024-11-05", "2025-03-26", "2025-06-18"})
DEPRECATED_PROTOCOLS = frozenset({"2024-11-05"})

SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

# Compatibility matrix: (client_major, protocol_version)
SUPPORTED_COMPATIBILITY_MATRIX = {
    ("1", "2025-06-18"),
    ("1", "2025-03-26"),
    ("0", "2024-11-05"),
}

CAPABILITY_SETS = {
    "2024-11-05": ["announce", "send", "inbox", "ack", "roster"],
    "2025-03-26": ["announce", "send", "inbox", "ack", "roster", "watch", "retire", "hint"],
    "2025-06-18": [
        "announce", "send", "inbox", "ack", "roster", "watch", "retire", "hint",
        "decision_request", "decision_status", "offer", "offer_inbox", "offer_reply",
        "offer_status", "offer_control", "assignment_transition", "memory_read", "memory_append", "prune", "imessage"
    ],
}


class BootstrapCompatibilityError(Exception):
    """Raised when a client fails compatibility boundary requirements."""
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def negotiate_protocol(requested_version: Optional[str]) -> Dict[str, Any]:
    """Negotiate protocol version with client.

    Fails closed if protocol version is missing, None, or unsupported.
    """
    if not requested_version or not isinstance(requested_version, str):
        raise BootstrapCompatibilityError("MISSING-PROTOCOL-VERSION", "Requested protocol version must be specified as a non-empty string.")

    if requested_version not in SUPPORTED_PROTOCOLS:
        raise BootstrapCompatibilityError(
            "UNSUPPORTED-PROTOCOL-VERSION",
            f"Requested protocol version {requested_version!r} is unsupported. Supported: {sorted(SUPPORTED_PROTOCOLS)}"
        )

    selected = requested_version
    is_deprecated = selected in DEPRECATED_PROTOCOLS
    is_stale = selected != PROTOCOL_VERSION_CURRENT
    tools = CAPABILITY_SETS.get(selected, [])

    guidance = []
    if is_deprecated:
        guidance.append(f"Protocol {selected} is deprecated. Please upgrade client to {PROTOCOL_VERSION_CURRENT}.")
    elif is_stale:
        guidance.append(f"Protocol {selected} is in maintenance mode. Recommended version: {PROTOCOL_VERSION_CURRENT}.")

    return {
        "status": "accepted",
        "protocol_version": selected,
        "current_version": PROTOCOL_VERSION_CURRENT,
        "supported_versions": sorted(SUPPORTED_PROTOCOLS),
        "is_stale": is_stale,
        "is_deprecated": is_deprecated,
        "available_tools": tools,
        "migration_guidance": guidance,
    }


def validate_client_bootstrap(client_info: Dict[str, Any]) -> Dict[str, Any]:
    """Validate client bootstrap handshake payload.

    Fails closed on missing, bogus, unsupported client information or incompatible (client, protocol) tuples.
    """
    if not isinstance(client_info, dict):
        raise BootstrapCompatibilityError("INVALID-CLIENT-PAYLOAD", "Client bootstrap handshake payload must be a JSON object.")

    client_name = client_info.get("name")
    client_version = client_info.get("version")
    proto = client_info.get("protocolVersion")

    if not client_name or not isinstance(client_name, str) or client_name == "unknown":
        raise BootstrapCompatibilityError("MISSING-CLIENT-NAME", "Client payload must declare a valid non-empty 'name'.")

    if not client_version or not isinstance(client_version, str) or not SEMVER_RE.fullmatch(client_version) or client_version == "0.0.0":
        raise BootstrapCompatibilityError("INVALID-CLIENT-VERSION", f"Client payload must declare a valid non-zero semantic version: {client_version!r}")

    # Validate protocol
    negotiation = negotiate_protocol(proto)

    # Validate compatibility matrix tuple (client_major, protocol)
    client_major = client_version.split(".")[0]
    if (client_major, proto) not in SUPPORTED_COMPATIBILITY_MATRIX:
        raise BootstrapCompatibilityError(
            "INCOMPATIBLE-CLIENT-PROTOCOL-TUPLE",
            f"Client version '{client_version}' (major {client_major}) is incompatible with protocol '{proto}'. Supported combinations: {sorted(SUPPORTED_COMPATIBILITY_MATRIX)}"
        )

    return {
        "status": "accepted",
        "client": {
            "name": client_name,
            "version": client_version,
        },
        "negotiation": negotiation,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-version", help="Client requested protocol version")
    parser.add_argument("--client-json", help="Raw JSON client handshake payload")
    parser.add_argument("--client-file", type=Path, help="Path to JSON file containing client handshake payload")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2

    try:
        if args.client_json or args.client_file:
            if args.client_json:
                try:
                    payload = json.loads(args.client_json)
                except Exception as err:
                    raise BootstrapCompatibilityError("MALFORMED-CLIENT-JSON", f"Failed to parse client JSON: {err}")
            else:
                try:
                    payload = json.loads(args.client_file.read_text(encoding="utf-8"))
                except Exception as err:
                    raise BootstrapCompatibilityError("MALFORMED-CLIENT-JSON", f"Failed to parse client file JSON: {err}")

            res = validate_client_bootstrap(payload)
            if args.json:
                sys.stdout.write(json.dumps(res, indent=2) + "\n")
            else:
                sys.stdout.write(f"Client Handshake: ACCEPTED ({res['client']['name']} v{res['client']['version']} on proto {res['negotiation']['protocol_version']})\n")
            return 0

        elif args.protocol_version:
            res = negotiate_protocol(args.protocol_version)
            if args.json:
                sys.stdout.write(json.dumps(res, indent=2) + "\n")
            else:
                sys.stdout.write(f"Negotiated Protocol: {res['protocol_version']} (Current: {res['current_version']})\n")
                if res["is_stale"]:
                    sys.stdout.write(f"Warning: Client protocol is stale. {res['migration_guidance']}\n")
            return 0
        else:
            raise BootstrapCompatibilityError("MISSING-ARGUMENTS", "Either --protocol-version or --client-json/--client-file must be provided.")

    except BootstrapCompatibilityError as err:
        if args.json:
            err_dict = {
                "status": "rejected",
                "error_code": err.code,
                "message": err.message,
            }
            sys.stdout.write(json.dumps(err_dict, indent=2) + "\n")
        else:
            sys.stderr.write(f"Bootstrap Compatibility Error [{err.code}]: {err.message}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
