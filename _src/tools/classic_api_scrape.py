#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""classic_api_scrape.py — C-API-Funktionsdeklarationen aus AUTOSAR-Classic-SWS-PDFs extrahieren.

Zweck
-----
Extrahiert aus den normativen AUTOSAR-Classic-SWS-PDFs (unter _src/spec/pdf-cache/R20-11/AUTOSAR/CLASSIC/)
alle C-API-Funktionsdefinitionen aus Kapitel 8 (API specification, Scheduled functions, Call-back notifications).
Befüllt oder synchronisiert damit die Spezifikations-Records unter _src/spec/records/classic/CP_*.json.

Aufrufbeispiele
---------------
    python3 _src/tools/classic_api_scrape.py list
    python3 _src/tools/classic_api_scrape.py extract --pdf AUTOSAR_SWS_CANInterface.pdf
    python3 _src/tools/classic_api_scrape.py extract --cluster CAN
    python3 _src/tools/classic_api_scrape.py check
    python3 _src/tools/classic_api_scrape.py rebuild --cluster CAN
    python3 _src/tools/classic_api_scrape.py rebuild --all
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_TOOLS_DIR = Path(__file__).resolve().parent
_SRC_DIR = _TOOLS_DIR.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import spec_scrape

LOG = logging.getLogger("classic_api_scrape")
if not LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    LOG.addHandler(_h)
LOG.setLevel(logging.INFO)

DEFAULT_CACHE_DIR = _SRC_DIR / "spec" / "pdf-cache" / "R20-11" / "AUTOSAR" / "CLASSIC"
RECORDS_DIR = _SRC_DIR / "spec" / "records" / "classic"
MODULES_RECORDS_DIR = RECORDS_DIR / "modules"
MODULES_PAGES_DIR = _SRC_DIR / "sources" / "pages" / "classic" / "modules"
PAGES_DIR = _SRC_DIR / "sources" / "pages" / "classic"

CLUSTER_PAGE_MAP = {
    "CAN": "can.html",
    "LIN": "lin.html",
    "FR": "flexray.html",
    "COM": "com.html",
    "DIAG": "diagnostics.html",
    "ETH": "ethernet.html",
    "SYS": "system.html",
    "OS": "os.html",
    "MEM": "memory.html",
    "CRYPTO": "crypto.html",
    "SEC": "security.html",
    "MCAL": "mcal.html",
    "RTE": "rte.html",
    "TYPES": "types.html",
}

CLUSTER_TITLE_MAP = {
    "CAN": "CAN",
    "LIN": "LIN",
    "FR": "FlexRay",
    "COM": "Communication Services",
    "DIAG": "Diagnostic Services",
    "ETH": "Ethernet Services",
    "SYS": "System Services",
    "OS": "Operating System",
    "MEM": "Memory Services",
    "CRYPTO": "Crypto Services",
    "SEC": "Security & Intrusion Detection",
    "MCAL": "Microcontroller Abstraction (MCAL)",
    "RTE": "Runtime Environment (RTE)",
    "TYPES": "General & Standard Types",
}

CLUSTER_OVERVIEW_MAP = {
    "CAN": "Das CAN-Cluster (Controller Area Network) stellt hardwarenahe Treiber, standardisierte Hardware-Abstraktion (CanIf), State-Management und ISO 15765-2 Transportprotokolle (CanTp) für klassische CAN-, CAN FD- und CAN XL-Netzwerke bereit.",
    "LIN": "Das LIN-Cluster umfasst Low-Cost-Subbus-Kommunikation für Karosserie- und Komfortfunktionen inklusive Treiber, LinIf-Schedule-Tabellen-Handling, Transceiver-Steuerung und State-Management.",
    "FR": "Das FlexRay-Cluster bietet deterministische, fehlertolerante High-Speed-Kommunikation mit statischen und dynamischen Segmenten, Bus-Synchronisation, ISO 10681 Transportprotokoll und Transceiver-Diagnose.",
    "COM": "Die Communication Services bilden das nachrichten- und signalbasierte Rückgrat der BSW: Signalextraktion, PDU-Routing ohne Payload-Inspektion (PduR) und ECU-weites Kommunikations- und Kanalmanagement (ComM).",
    "DIAG": "Die Diagnostic Services der AUTOSAR Classic Platform implementieren normierte Diagnoseprotokolle nach ISO 14229 (UDS) und ISO 15765-4 (OBD), Fehlererkennung und -speicherung im Fehlerspeicher (DEM), Entwicklungsfehler-Tracing (DET) sowie strukturiertes Logging (DLT).",
    "ETH": "Das Ethernet-Cluster realisiert IP-basierte Fahrzeugvernetzung, BroadR-Reach/100BASE-T1 Kommunikation, TCP/UDP-Stacks, IPv4/IPv6-Adressierung und Service-orientierte Schnittstellen.",
    "SYS": "Die System Services steuern den gesamten ECU-Lebenszyklus von Power-On über Wakeup, Betriebszustände, Modus-Arbitrierung (BswM) bis zum sicheren Herunterfahren und Programmlauf-Überwachung (WdgM).",
    "OS": "Das AUTOSAR Operating System ist ein statisch konfiguriertes, echtzeitfähiges preemptives Betriebssystem nach OSEK/VDX mit Tasks, Events, Alarmen, Schedule-Tables und Speicherschutz.",
    "MEM": "Die Memory Services verwalten nicht-flüchtige Datenblöcke (NvM), abstrahieren Flash- und EEPROM-Technologien (MemIf, Fee, Ea) und gewährleisten Datenkonsistenz und Datensicherheit über ECU-Abschaltzyklen hinweg.",
    "CRYPTO": "Die Crypto Services bieten hardware- und softwaregestützte Kryptographie-Primitive (CSM, CryIf, Crypto-Treiber) für symmetrische/asymmetrische Verschlüsselung, Signaturen und Hashing.",
    "SEC": "Das Security-Cluster schützt vernetzte Fahrzeugfunktionen gegen Cyber-Bedrohungen durch Intrusion Detection (IdsM), kryptographische PDU-Authentifizierung und Freshness-Protection (SecOC) sowie Key- und Zertifikatsmanagement (KeyM).",
    "MCAL": "Die Microcontroller Abstraction Layer (MCAL) enthält hardware-spezifische Treiber für interne Mikrocontroller-Peripherie (ADC-Wandler, PWM-Generatoren, Hardware-Watchdog) und entkoppelt obere BSW-Schichten von der Silizium-Plattform.",
    "RTE": "Die Runtime Environment (RTE) realisiert den Virtual Functional Bus (VFB) auf einer konkreten ECU und vermittelt alle Inter- und Intra-ECU-Kommunikationsverbindungen zwischen Software-Components (SW-Cs) und Basis-Software.",
    "TYPES": "Die Standard- und Plattformtypen definieren die grundlegenden C-Typen, Rückgabewerte und Kommunikationsdatenstrukturen der AUTOSAR Classic Architektur. Sie stellen hardwareunabhängige Portabilität für Basissoftware und Applikations-SW-Cs sicher.",
}

# Zuordnung: Cluster-Schlüssel -> Metadaten, Ziel-Record und Quelldokumente
CLUSTER_MAP = OrderedDict([
    ("CAN", {
        "record": "CP_CAN.json",
        "title": "CAN Cluster (Driver, Interface, Transceiver, Transport Layer)",
        "modules": OrderedDict([
            ("Can", {
                "heading": "CAN Driver (Can)",
                "lead": "The CAN driver provides hardware-dependent access to the internal and external CAN controllers (CAN 2.0B, CAN FD, CAN XL).",
                "pdf": "AUTOSAR_SWS_CANDriver.pdf",
            }),
            ("CanIf", {
                "heading": "CAN Interface (CanIf)",
                "lead": "The CanIf abstracts CAN hardware details and provides uniform access to multiple CAN controllers and transceivers for higher-layer modules (PduR, CanTp, CanNm, CanSM).",
                "pdf": "AUTOSAR_SWS_CANInterface.pdf",
            }),
            ("CanTrcv", {
                "heading": "CAN Transceiver Driver (CanTrcv)",
                "lead": "Controls physical bus transceiver states and wakeup detection on CAN lines.",
                "pdf": "AUTOSAR_SWS_CANTransceiverDriver.pdf",
            }),
            ("CanTp", {
                "heading": "CAN Transport Layer (CanTp)",
                "lead": "Provides segmentation and reassembly of CAN messages up to 4095 bytes (ISO 15765-2).",
                "pdf": "AUTOSAR_SWS_CANTransportLayer.pdf",
            }),
        ]),
    }),
    ("LIN", {
        "record": "CP_LIN.json",
        "title": "LIN Cluster (Driver, Interface, State Manager, Transceiver)",
        "modules": OrderedDict([
            ("Lin", {
                "heading": "LIN Driver (Lin)",
                "lead": "Controls hardware LIN controllers on the ECU.",
                "pdf": "AUTOSAR_SWS_LINDriver.pdf",
            }),
            ("LinIf", {
                "heading": "LIN Interface (LinIf)",
                "lead": "Abstracts LIN hardware and manages schedule tables and frame transmission.",
                "pdf": "AUTOSAR_SWS_LINInterface.pdf",
            }),
            ("LinSM", {
                "heading": "LIN State Manager (LinSM)",
                "lead": "Manages state transitions of LIN networks.",
                "pdf": "AUTOSAR_SWS_LINStateManager.pdf",
            }),
            ("LinTrcv", {
                "heading": "LIN Transceiver Driver (LinTrcv)",
                "lead": "Controls physical bus transceiver states and wakeup on LIN lines.",
                "pdf": "AUTOSAR_SWS_LINTransceiverDriver.pdf",
            }),
        ]),
    }),
    ("FR", {
        "record": "CP_FR.json",
        "title": "FlexRay Cluster (Driver, Interface, State Manager, Transport Layer, Transceiver)",
        "modules": OrderedDict([
            ("Fr", {
                "heading": "FlexRay Driver (Fr)",
                "lead": "Provides hardware-dependent access to FlexRay communication controllers.",
                "pdf": "AUTOSAR_SWS_FlexRayDriver.pdf",
            }),
            ("FrIf", {
                "heading": "FlexRay Interface (FrIf)",
                "lead": "Abstracts FlexRay hardware controllers for upper layers.",
                "pdf": "AUTOSAR_SWS_FlexRayInterface.pdf",
            }),
            ("FrSM", {
                "heading": "FlexRay State Manager (FrSM)",
                "lead": "Controls the operational states and startup/wakeup of FlexRay clusters.",
                "pdf": "AUTOSAR_SWS_FlexRayStateManager.pdf",
            }),
            ("FrTp", {
                "heading": "FlexRay Transport Layer (FrTp)",
                "lead": "Provides segmented data transmission over FlexRay (ISO 10681-2).",
                "pdf": "AUTOSAR_SWS_FlexRayISOTransportLayer.pdf",
            }),
            ("FrTrcv", {
                "heading": "FlexRay Transceiver Driver (FrTrcv)",
                "lead": "Controls physical bus transceiver states and bus diagnostics on FlexRay lines.",
                "pdf": "AUTOSAR_SWS_FlexRayTransceiverDriver.pdf",
            }),
        ]),
    }),
    ("COM", {
        "record": "CP_COM.json",
        "title": "Communication Services (COM, PDU Router, COM Manager)",
        "modules": OrderedDict([
            ("Com", {
                "heading": "AUTOSAR COM",
                "lead": "The AUTOSAR COM module provides signal-based communication services for inter-ECU exchange across diverse bus systems.",
                "pdf": "AUTOSAR_SWS_COM.pdf",
            }),
            ("PduR", {
                "heading": "PDU Router (PduR)",
                "lead": "The PDU Router routes I-PDUs between communication interfaces, transport protocols, and upper layers without payload inspection.",
                "pdf": "AUTOSAR_SWS_PDURouter.pdf",
            }),
            ("ComM", {
                "heading": "Communication Manager (ComM)",
                "lead": "Manages communication states and channel modes across multiple network interfaces.",
                "pdf": "AUTOSAR_SWS_COMManager.pdf",
            }),
        ]),
    }),
    ("DIAG", {
        "record": "CP_DIAG.json",
        "title": "Diagnostic Services (DEM, DCM, DET, DLT)",
        "modules": OrderedDict([
            ("Dem", {
                "heading": "Diagnostic Event Manager (DEM)",
                "lead": "The DEM is responsible for processing and storing diagnostic events, fault memories, DTC statuses, and associated freeze frame data.",
                "pdf": "AUTOSAR_SWS_DiagnosticEventManager.pdf",
            }),
            ("Dcm", {
                "heading": "Diagnostic Communication Manager (DCM)",
                "lead": "The DCM implements unified diagnostic services according to ISO 14229-1 (UDS) and ISO 15765-4 (OBD). It manages diagnostic sessions, security levels, and service routing.",
                "pdf": "AUTOSAR_SWS_DiagnosticCommunicationManager.pdf",
            }),
            ("Det", {
                "heading": "Default Error Tracer (DET)",
                "lead": "The DET handles development errors, runtime errors, and transient faults across all BSW modules and SW-Cs.",
                "pdf": "AUTOSAR_SWS_DefaultErrorTracer.pdf",
            }),
            ("Dlt", {
                "heading": "Diagnostic Log and Trace (DLT)",
                "lead": "The DLT module collects log messages and trace points and formats them into standardized DLT frames for external tooling.",
                "pdf": "AUTOSAR_SWS_DiagnosticLogAndTrace.pdf",
            }),
        ]),
    }),
    ("ETH", {
        "record": "CP_ETH.json",
        "title": "Ethernet Services (Ethernet Driver, Ethernet Interface, TCP/IP)",
        "modules": OrderedDict([
            ("Eth", {
                "heading": "Ethernet Driver (Eth)",
                "lead": "Provides uniform hardware access to Ethernet controller interfaces.",
                "pdf": "AUTOSAR_SWS_EthernetDriver.pdf",
            }),
            ("EthIf", {
                "heading": "Ethernet Interface (EthIf)",
                "lead": "Abstracts Ethernet controller and transceiver hardware for upper protocol layers.",
                "pdf": "AUTOSAR_SWS_EthernetInterface.pdf",
            }),
            ("TcpIp", {
                "heading": "TCP/IP Stack (TcpIp)",
                "lead": "Provides IPv4/IPv6 networking, TCP/UDP sockets, ARP, ICMP, and DHCP services.",
                "pdf": "AUTOSAR_SWS_TcpIp.pdf",
            }),
        ]),
    }),
    ("SYS", {
        "record": "CP_SYS.json",
        "title": "System Services (ECU State Manager, BSW Mode Manager, Watchdog Manager)",
        "modules": OrderedDict([
            ("EcuM", {
                "heading": "ECU State Manager (EcuM)",
                "lead": "Controls ECU lifecycle states: Startup, Run, PostRun, Sleep, and Shutdown.",
                "pdf": "AUTOSAR_SWS_ECUStateManager.pdf",
            }),
            ("BswM", {
                "heading": "BSW Mode Manager (BswM)",
                "lead": "Arbitrates mode requests and executes action lists to control system state transitions.",
                "pdf": "AUTOSAR_SWS_BSWModeManager.pdf",
            }),
            ("WdgM", {
                "heading": "Watchdog Manager (WdgM)",
                "lead": "Performs alive supervision, deadline supervision, and logical program flow monitoring.",
                "pdf": "AUTOSAR_SWS_WatchdogManager.pdf",
            }),
        ]),
    }),
    ("OS", {
        "record": "CP_OS.json",
        "title": "Operating System",
        "modules": OrderedDict([
            ("Os", {
                "heading": "AUTOSAR OS",
                "lead": "Real-time operating system managing priority-based preemptive task scheduling, events, alarms, and schedule tables (OSEK/VDX derivative).",
                "pdf": "AUTOSAR_SWS_OS.pdf",
            }),
        ]),
    }),
    ("MEM", {
        "record": "CP_MEM.json",
        "title": "Memory Services (NVRAM Manager, MemIf, Fee, Ea)",
        "modules": OrderedDict([
            ("NvM", {
                "heading": "NVRAM Manager (NvM)",
                "lead": "Provides synchronous and asynchronous block-based data management for non-volatile storage (EEPROM, Flash).",
                "pdf": "AUTOSAR_SWS_NVRAMManager.pdf",
            }),
            ("MemIf", {
                "heading": "Memory Abstraction Interface (MemIf)",
                "lead": "Abstracts underlying Flash and EEPROM memory drivers.",
                "pdf": "AUTOSAR_SWS_MemoryAbstractionInterface.pdf",
            }),
            ("Fee", {
                "heading": "Flash EEPROM Emulation (Fee)",
                "lead": "Provides emulation of EEPROM-like data blocks on Flash memory devices.",
                "pdf": "AUTOSAR_SWS_FlashEEPROMEmulation.pdf",
            }),
            ("Ea", {
                "heading": "EEPROM Abstraction (Ea)",
                "lead": "Provides uniform access to external and internal EEPROM devices.",
                "pdf": "AUTOSAR_SWS_EEPROMAbstraction.pdf",
            }),
        ]),
    }),
    ("CRYPTO", {
        "record": "CP_CRYPTO.json",
        "title": "Security & Cryptography (CSM, CryIf, Crypto)",
        "modules": OrderedDict([
            ("Csm", {
                "heading": "Crypto Service Manager (CSM)",
                "lead": "Provides standardized cryptographic services (encryption, hashing, digital signatures, key management) to applications and BSW.",
                "pdf": "AUTOSAR_SWS_CryptoServiceManager.pdf",
            }),
            ("CryIf", {
                "heading": "Crypto Interface (CryIf)",
                "lead": "Abstracts cryptographic hardware and software acceleration engines.",
                "pdf": "AUTOSAR_SWS_CryptoInterface.pdf",
            }),
            ("Crypto", {
                "heading": "Crypto Driver (Crypto)",
                "lead": "Low-level driver executing cryptographic primitives on hardware security modules (HSM) or software libraries.",
                "pdf": "AUTOSAR_SWS_CryptoDriver.pdf",
            }),
        ]),
    }),
    ("SEC", {
        "record": "CP_SEC.json",
        "title": "Security & Intrusion Detection (IdsM, SecOC, KeyM)",
        "modules": OrderedDict([
            ("IdsM", {
                "heading": "Intrusion Detection System Manager (IdsM)",
                "lead": "Collects and reports onboard security events to detect threats.",
                "pdf": "AUTOSAR_SWS_IntrusionDetectionSystemManager.pdf",
            }),
            ("SecOC", {
                "heading": "Secure Onboard Communication (SecOC)",
                "lead": "Provides cryptographic authentication and freshness protection for critical communication PDUs.",
                "pdf": "AUTOSAR_SWS_SecureOnboardCommunication.pdf",
            }),
            ("KeyM", {
                "heading": "Key Manager (KeyM)",
                "lead": "Manages lifecycle, storage, and distribution of cryptographic keys and certificates.",
                "pdf": "AUTOSAR_SWS_KeyManager.pdf",
            }),
        ]),
    }),
    ("MCAL", {
        "record": "CP_MCAL.json",
        "title": "Microcontroller Abstraction Layer (MCAL)",
        "modules": OrderedDict([
            ("Adc", {
                "heading": "ADC Driver (Adc)",
                "lead": "Provides initialization and conversion services for analog-to-digital converters.",
                "pdf": "AUTOSAR_SWS_ADCDriver.pdf",
            }),
            ("Pwm", {
                "heading": "PWM Driver (Pwm)",
                "lead": "Generates pulse-width-modulated signals with configurable duty cycle and period.",
                "pdf": "AUTOSAR_SWS_PWMDriver.pdf",
            }),
            ("Wdg", {
                "heading": "Watchdog Driver (Wdg)",
                "lead": "Hardware watchdog timer servicing and mode configuration.",
                "pdf": "AUTOSAR_SWS_WatchdogDriver.pdf",
            }),
        ]),
    }),
    ("RTE", {
        "record": "CP_RTE.json",
        "title": "Runtime Environment (RTE)",
        "modules": OrderedDict([
            ("Rte", {
                "heading": "AUTOSAR RTE",
                "lead": "The RTE realizes the Virtual Functional Bus (VFB) on a specific ECU, providing communication between Software Components and basic software.",
                "pdf": "AUTOSAR_SWS_RTE.pdf",
            }),
        ]),
    }),
    ("TYPES", {
        "record": "CP_TYPES.json",
        "title": "General & Standard Types (Platform, Std, ComStack)",
        "modules": OrderedDict([
            ("Platform", {
                "heading": "Platform Types (Platform_Types)",
                "lead": "Platform-specific fundamental data types (integers, booleans, floating-point numbers) mapped to CPU architecture primitives.",
                "pdf": "AUTOSAR_SWS_PlatformTypes.pdf",
            }),
            ("Std", {
                "heading": "Standard Types (Std_Types)",
                "lead": "Standard types, return codes (Std_ReturnType, E_OK, E_NOT_OK), version info structures, and error codes shared across the entire AUTOSAR architecture.",
                "pdf": "AUTOSAR_SWS_StandardTypes.pdf",
            }),
            ("ComStack", {
                "heading": "Communication Stack Types (ComStack_Types)",
                "lead": "Standardized types, PDU identifiers, lengths, and buffer request types (PduIdType, PduLengthType, PduInfoType, BufReq_ReturnType) used across all communication layers.",
                "pdf": "AUTOSAR_SWS_CommunicationStackTypes.pdf",
            }),
        ]),
    }),
])


BSW_METADATA = {
    "Can": {"name": "CAN Driver", "bsw_id": 80, "header": "Can.h"},
    "CanIf": {"name": "CAN Interface", "bsw_id": 60, "header": "CanIf.h"},
    "CanTrcv": {"name": "CAN Transceiver Driver", "bsw_id": 70, "header": "CanTrcv.h"},
    "CanTp": {"name": "CAN Transport Layer", "bsw_id": 35, "header": "CanTp.h"},

    "Lin": {"name": "LIN Driver", "bsw_id": 82, "header": "Lin.h"},
    "LinIf": {"name": "LIN Interface", "bsw_id": 62, "header": "LinIf.h"},
    "LinSM": {"name": "LIN State Manager", "bsw_id": 141, "header": "LinSM.h"},
    "LinTrcv": {"name": "LIN Transceiver Driver", "bsw_id": 64, "header": "LinTrcv.h"},

    "Fr": {"name": "FlexRay Driver", "bsw_id": 81, "header": "Fr.h"},
    "FrIf": {"name": "FlexRay Interface", "bsw_id": 61, "header": "FrIf.h"},
    "FrSM": {"name": "FlexRay State Manager", "bsw_id": 142, "header": "FrSM.h"},
    "FrTp": {"name": "FlexRay Transport Layer", "bsw_id": 36, "header": "FrTp.h"},
    "FrTrcv": {"name": "FlexRay Transceiver Driver", "bsw_id": 71, "header": "FrTrcv.h"},

    "Com": {"name": "AUTOSAR COM", "bsw_id": 50, "header": "Com.h"},
    "PduR": {"name": "PDU Router", "bsw_id": 51, "header": "PduR.h"},
    "ComM": {"name": "Communication Manager", "bsw_id": 12, "header": "ComM.h"},

    "Dem": {"name": "Diagnostic Event Manager", "bsw_id": 54, "header": "Dem.h"},
    "Dcm": {"name": "Diagnostic Communication Manager", "bsw_id": 53, "header": "Dcm.h"},
    "Det": {"name": "Default Error Tracer", "bsw_id": 15, "header": "Det.h"},
    "Dlt": {"name": "Diagnostic Log and Trace", "bsw_id": 55, "header": "Dlt.h"},

    "Eth": {"name": "Ethernet Driver", "bsw_id": 88, "header": "Eth.h"},
    "EthIf": {"name": "Ethernet Interface", "bsw_id": 65, "header": "EthIf.h"},
    "TcpIp": {"name": "TCP/IP Stack", "bsw_id": 170, "header": "TcpIp.h"},

    "EcuM": {"name": "ECU State Manager", "bsw_id": 10, "header": "EcuM.h"},
    "BswM": {"name": "BSW Mode Manager", "bsw_id": 42, "header": "BswM.h"},
    "WdgM": {"name": "Watchdog Manager", "bsw_id": 13, "header": "WdgM.h"},

    "Os": {"name": "AUTOSAR OS", "bsw_id": 1, "header": "Os.h"},

    "NvM": {"name": "NVRAM Manager", "bsw_id": 20, "header": "NvM.h"},
    "MemIf": {"name": "Memory Abstraction Interface", "bsw_id": 22, "header": "MemIf.h"},
    "Fee": {"name": "Flash EEPROM Emulation", "bsw_id": 40, "header": "Fee.h"},
    "Ea": {"name": "EEPROM Abstraction", "bsw_id": 41, "header": "Ea.h"},

    "Csm": {"name": "Crypto Service Manager", "bsw_id": 110, "header": "Csm.h"},
    "CryIf": {"name": "Crypto Interface", "bsw_id": 112, "header": "CryIf.h"},
    "Crypto": {"name": "Crypto Driver", "bsw_id": 114, "header": "Crypto.h"},

    "IdsM": {"name": "Intrusion Detection System Manager", "bsw_id": 252, "header": "IdsM.h"},
    "SecOC": {"name": "Secure Onboard Communication", "bsw_id": 150, "header": "SecOC.h"},
    "KeyM": {"name": "Key Manager", "bsw_id": 113, "header": "KeyM.h"},

    "Adc": {"name": "ADC Driver", "bsw_id": 123, "header": "Adc.h"},
    "Pwm": {"name": "PWM Driver", "bsw_id": 121, "header": "Pwm.h"},
    "Wdg": {"name": "Watchdog Driver", "bsw_id": 102, "header": "Wdg.h"},

    "Rte": {"name": "Runtime Environment", "bsw_id": 2, "header": "Rte.h"},

    "Platform": {"name": "Platform Types", "bsw_id": 199, "header": "Platform_Types.h"},
    "Std": {"name": "Standard Types", "bsw_id": 197, "header": "Std_Types.h"},
    "ComStack": {"name": "Communication Stack Types", "bsw_id": 196, "header": "ComStack_Types.h"},
}

# Enrich CLUSTER_MAP with BSW_METADATA
for _cname, _cinfo in CLUSTER_MAP.items():
    for _mkey, _minfo in _cinfo["modules"].items():
        if _mkey in BSW_METADATA:
            _minfo.update(BSW_METADATA[_mkey])

TABLE_KEYS = [
    "Service Name", "Name", "Syntax", "Service ID [hex]", "Service ID",
    "Sync/Async", "Reentrancy", "Parameters (inout)", "Parameters (in)",
    "Parameters (out)", "Return value", "Kind", "Derived from", "Derived From",
    "Derived", "Basetype", "Elements", "Range", "Variation", "Comment",
    "Description", "Available via"
]

VALID_TYPE_KINDS = {
    "type", "structure", "enumeration", "bitfield", "array", "pointer",
    "function pointer", "const", "mode"
}

# ---------------------------------------------------------------------------
# AUTOSAR Classic Type Registry & Linking Engine (Requirement 3)
# ---------------------------------------------------------------------------

CLUSTER_TO_PAGE: Dict[str, str] = {
    "CAN": "can.html",
    "LIN": "lin.html",
    "FR": "flexray.html",
    "COM": "com.html",
    "DIAG": "diagnostics.html",
    "ETH": "ethernet.html",
    "SYS": "system.html",
    "OS": "os.html",
    "MEM": "memory.html",
    "CRYPTO": "crypto.html",
    "SEC": "security.html",
    "MCAL": "mcal.html",
    "RTE": "rte.html",
    "TYPES": "types.html",
}

MODULE_TO_PAGE: Dict[str, str] = {}
for _cname, _cinfo in CLUSTER_MAP.items():
    for _mkey in _cinfo["modules"]:
        MODULE_TO_PAGE[_mkey.lower()] = f"{_mkey.lower()}.html"
for _mkey in BSW_METADATA:
    MODULE_TO_PAGE[_mkey.lower()] = f"{_mkey.lower()}.html"


class ClassicTypeEntry:
    """Represents a registered AUTOSAR Classic type definition with linking metadata."""

    def __init__(
        self,
        name: str,
        sws_id: str,
        module: str,
        cluster: str = "",
        category: str = "bsw",
        url: str = "",
        desc: str = "",
        type_kind: str = "type",
    ):
        self.name = name
        self.sws_id = sws_id
        self.module = module
        self.cluster = cluster
        self.category = category  # "standard_platform" or "bsw"
        self._url = url
        self.desc = desc
        self.type_kind = type_kind

    @property
    def url(self) -> str:
        if self._url:
            return self._url
        page = MODULE_TO_PAGE.get(self.module.lower(), f"{self.module.lower()}.html")
        if page:
            return f"{page}#{self.sws_id}"
        return f"#{self.sws_id}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "sws_id": self.sws_id,
            "module": self.module,
            "cluster": self.cluster,
            "category": self.category,
            "url": self.url,
            "desc": self.desc,
            "type_kind": self.type_kind,
        }

    def __repr__(self) -> str:
        return f"ClassicTypeEntry(name={self.name!r}, sws_id={self.sws_id!r}, module={self.module!r}, category={self.category!r})"


KNOWN_TYPE_SYNTAX: Dict[str, str] = {
    # Platform Types (Platform_Types.h)
    "boolean": "typedef unsigned char boolean;",
    "uint8": "typedef unsigned char uint8;",
    "uint16": "typedef unsigned short uint16;",
    "uint32": "typedef unsigned long uint32;",
    "uint64": "typedef unsigned long long uint64;",
    "sint8": "typedef signed char sint8;",
    "sint16": "typedef signed short sint16;",
    "sint32": "typedef signed long sint32;",
    "sint64": "typedef signed long long sint64;",
    "uint8_least": "typedef unsigned int uint8_least;",
    "uint16_least": "typedef unsigned int uint16_least;",
    "uint32_least": "typedef unsigned int uint32_least;",
    "sint8_least": "typedef signed int sint8_least;",
    "sint16_least": "typedef signed int sint16_least;",
    "sint32_least": "typedef signed int sint32_least;",
    "float32": "typedef float float32;",
    "float64": "typedef double float64;",
    "VoidPtr": "typedef void* VoidPtr;",
    "ConstVoidPtr": "typedef const void* ConstVoidPtr;",

    # Standard Types (Std_Types.h)
    "Std_ReturnType": "typedef uint8 Std_ReturnType;",
    "Std_VersionInfoType": "typedef struct {\n    uint16 vendorID;\n    uint16 moduleID;\n    uint8 sw_major_version;\n    uint8 sw_minor_version;\n    uint8 sw_patch_version;\n} Std_VersionInfoType;",
    "Std_TransformerError": "typedef uint8 Std_TransformerError;",
    "Std_TransformerClass": "typedef uint8 Std_TransformerClass;",
    "Std_TransformerForward": "typedef uint8 Std_TransformerForward;",
    "Std_TransformerForwardCode": "typedef uint8 Std_TransformerForwardCode;",
    "Std_MessageTypeType": "typedef uint8 Std_MessageTypeType;",
    "Std_MessageResultType": "typedef uint8 Std_MessageResultType;",
    "Std_ExtractProtocolHeaderFieldsType": "typedef Std_ReturnType (*Std_ExtractProtocolHeaderFieldsType)(const uint8* buffer, uint32 bufferLength, Std_MessageTypeType* messageType, Std_MessageResultType* messageResult);",
    "E_OK / E_NOT_OK": "#define E_OK 0x00u\n#define E_NOT_OK 0x01u",
    "STD_HIGH / STD_LOW": "#define STD_HIGH 0x01u\n#define STD_LOW 0x00u",
    "STD_ON / STD_OFF": "#define STD_ON 0x01u\n#define STD_OFF 0x00u",
    "STD_ACTIVE / STD_IDLE": "#define STD_ACTIVE 0x01u\n#define STD_IDLE 0x00u",

    # Communication Stack Types (ComStack_Types.h)
    "PduIdType": "typedef uint16 PduIdType;",
    "PduLengthType": "typedef uint16 PduLengthType;",
    "PduInfoType": "typedef struct {\n    uint8* SduDataPtr;\n    uint8* MetaDataPtr;\n    PduLengthType SduLength;\n} PduInfoType;",
    "BufReq_ReturnType": "typedef enum {\n    BUFREQ_OK,\n    BUFREQ_E_NOT_OK,\n    BUFREQ_E_BUSY,\n    BUFREQ_E_OVFL\n} BufReq_ReturnType;",
    "NetworkHandleType": "typedef uint8 NetworkHandleType;",
    "PNCHandleType": "typedef uint8 PNCHandleType;",
    "TpDataStateType": "typedef enum {\n    TP_DATACONF,\n    TP_DATARETRY,\n    TP_CONFPENDING\n} TpDataStateType;",
    "RetryInfoType": "typedef struct {\n    TpDataStateType TpDataState;\n    PduLengthType TxTpDataCnt;\n} RetryInfoType;",
    "TPParameterType": "typedef enum {\n    TP_STMIN,\n    TP_BS,\n    TP_BC\n} TPParameterType;",

    # OS Base Types (Os.h / OSEK)
    "TickType": "typedef uint32 TickType;",
    "StatusType": "typedef uint8 StatusType;",
    "TaskType": "typedef uint8 TaskType;",
    "EventMaskType": "typedef uint32 EventMaskType;",
    "AlarmType": "typedef uint8 AlarmType;",
}


OS_BASE_TYPES: List[Dict[str, Any]] = [
    {
        "id": "SWS_Os_00001",
        "name": "TickType",
        "kind": "type",
        "syntax": "typedef uint32 TickType;",
        "desc": "This data type represents count values in ticks.",
        "header": "Os.h",
        "type_kind": "Type",
        "page": 1,
    },
    {
        "id": "SWS_Os_00002",
        "name": "StatusType",
        "kind": "type",
        "syntax": "typedef uint8 StatusType;",
        "desc": "This data type represents standard OSEK OS status codes (e.g. E_OK, E_OS_ACCESS).",
        "header": "Os.h",
        "type_kind": "Type",
        "page": 1,
    },
    {
        "id": "SWS_Os_00003",
        "name": "TaskType",
        "kind": "type",
        "syntax": "typedef uint8 TaskType;",
        "desc": "This data type identifies an AUTOSAR OS task.",
        "header": "Os.h",
        "type_kind": "Type",
        "page": 1,
    },
    {
        "id": "SWS_Os_00004",
        "name": "EventMaskType",
        "kind": "type",
        "syntax": "typedef uint32 EventMaskType;",
        "desc": "This data type represents an event mask for extended tasks.",
        "header": "Os.h",
        "type_kind": "Type",
        "page": 1,
    },
    {
        "id": "SWS_Os_00005",
        "name": "AlarmType",
        "kind": "type",
        "syntax": "typedef uint8 AlarmType;",
        "desc": "This data type represents an AUTOSAR OS alarm identifier.",
        "header": "Os.h",
        "type_kind": "Type",
        "page": 1,
    },
]


STANDARD_PLATFORM_TYPES: Dict[str, Tuple[str, str, str]] = {
    # Platform Types (AUTOSAR_SWS_PlatformTypes.pdf -> Platform)
    "boolean": ("Platform", "SWS_Platform_00026", "platform.html#SWS_Platform_00026"),
    "uint8": ("Platform", "SWS_Platform_00013", "platform.html#SWS_Platform_00013"),
    "uint16": ("Platform", "SWS_Platform_00014", "platform.html#SWS_Platform_00014"),
    "uint32": ("Platform", "SWS_Platform_00015", "platform.html#SWS_Platform_00015"),
    "uint64": ("Platform", "SWS_Platform_00066", "platform.html#SWS_Platform_00066"),
    "sint8": ("Platform", "SWS_Platform_00016", "platform.html#SWS_Platform_00016"),
    "sint16": ("Platform", "SWS_Platform_00017", "platform.html#SWS_Platform_00017"),
    "sint32": ("Platform", "SWS_Platform_00018", "platform.html#SWS_Platform_00018"),
    "sint64": ("Platform", "SWS_Platform_00067", "platform.html#SWS_Platform_00067"),
    "uint8_least": ("Platform", "SWS_Platform_00020", "platform.html#SWS_Platform_00020"),
    "uint16_least": ("Platform", "SWS_Platform_00021", "platform.html#SWS_Platform_00021"),
    "uint32_least": ("Platform", "SWS_Platform_00022", "platform.html#SWS_Platform_00022"),
    "sint8_least": ("Platform", "SWS_Platform_00023", "platform.html#SWS_Platform_00023"),
    "sint16_least": ("Platform", "SWS_Platform_00024", "platform.html#SWS_Platform_00024"),
    "sint32_least": ("Platform", "SWS_Platform_00025", "platform.html#SWS_Platform_00025"),
    "float32": ("Platform", "SWS_Platform_00041", "platform.html#SWS_Platform_00041"),
    "float64": ("Platform", "SWS_Platform_00042", "platform.html#SWS_Platform_00042"),
    "VoidPtr": ("Platform", "SWS_Platform_91001", "platform.html#SWS_Platform_91001"),
    "ConstVoidPtr": ("Platform", "SWS_Platform_91002", "platform.html#SWS_Platform_91002"),

    # Standard Types (AUTOSAR_SWS_StandardTypes.pdf -> Std)
    "Std_ReturnType": ("Std", "SWS_Std_00005", "std.html#SWS_Std_00005"),
    "Std_VersionInfoType": ("Std", "SWS_Std_00015", "std.html#SWS_Std_00015"),
    "Std_TransformerError": ("Std", "SWS_Std_00021", "std.html#SWS_Std_00021"),
    "Std_TransformerClass": ("Std", "SWS_Std_00024", "std.html#SWS_Std_00024"),
    "Std_TransformerForward": ("Std", "SWS_Std_00027", "std.html#SWS_Std_00027"),
    "Std_TransformerForwardCode": ("Std", "SWS_Std_00029", "std.html#SWS_Std_00029"),
    "Std_MessageTypeType": ("Std", "SWS_Std_91001", "std.html#SWS_Std_91001"),
    "Std_MessageResultType": ("Std", "SWS_Std_91002", "std.html#SWS_Std_91002"),
    "Std_ExtractProtocolHeaderFieldsType": ("Std", "SWS_Std_91003", "std.html#SWS_Std_91003"),

    # Communication Stack Types (AUTOSAR_SWS_CommunicationStackTypes.pdf -> ComStack)
    "PduIdType": ("ComStack", "SWS_COMTYPE_00005", "comstack.html#SWS_COMTYPE_00005"),
    "PduLengthType": ("ComStack", "SWS_COMTYPE_00008", "comstack.html#SWS_COMTYPE_00008"),
    "PduInfoType": ("ComStack", "SWS_COMTYPE_00011", "comstack.html#SWS_COMTYPE_00011"),
    "BufReq_ReturnType": ("ComStack", "SWS_COMTYPE_00012", "comstack.html#SWS_COMTYPE_00012"),
    "NetworkHandleType": ("ComStack", "SWS_COMTYPE_00038", "comstack.html#SWS_COMTYPE_00038"),
    "TPParameterType": ("ComStack", "SWS_COMTYPE_00031", "comstack.html#SWS_COMTYPE_00031"),
    "PNCHandleType": ("ComStack", "SWS_COMTYPE_00036", "comstack.html#SWS_COMTYPE_00036"),
    "RetryInfoType": ("ComStack", "SWS_COMTYPE_00037", "comstack.html#SWS_COMTYPE_00037"),
    "TpDataStateType": ("ComStack", "SWS_COMTYPE_00027", "comstack.html#SWS_COMTYPE_00027"),

    # OS Platform Types (AUTOSAR_SWS_OS.pdf -> Os)
    "TickType": ("Os", "SWS_Os_00001", "os.html#SWS_Os_00001"),
    "StatusType": ("Os", "SWS_Os_00002", "os.html#SWS_Os_00002"),
    "TaskType": ("Os", "SWS_Os_00003", "os.html#SWS_Os_00003"),
    "EventMaskType": ("Os", "SWS_Os_00004", "os.html#SWS_Os_00004"),
    "AlarmType": ("Os", "SWS_Os_00005", "os.html#SWS_Os_00005"),
    "ScheduleTableType": ("Os", "SWS_Os_00783", "os.html#SWS_Os_00783"),
    "ScheduleTableStatusType": ("Os", "SWS_Os_00784", "os.html#SWS_Os_00784"),
    "ScheduleTableStatusRefType": ("Os", "SWS_Os_00785", "os.html#SWS_Os_00785"),
    "AppModeType": ("Os", "SWS_Os_91007", "os.html#SWS_Os_91007"),
    "ApplicationType": ("Os", "SWS_Os_00772", "os.html#SWS_Os_00772"),
    "ApplicationStateType": ("Os", "SWS_Os_00773", "os.html#SWS_Os_00773"),
    "ApplicationStateRefType": ("Os", "SWS_Os_00774", "os.html#SWS_Os_00774"),
    "TrustedFunctionIndexType": ("Os", "SWS_Os_00775", "os.html#SWS_Os_00775"),
    "TrustedFunctionParameterRefType": ("Os", "SWS_Os_00776", "os.html#SWS_Os_00776"),
    "AccessType": ("Os", "SWS_Os_00777", "os.html#SWS_Os_00777"),
    "ObjectAccessType": ("Os", "SWS_Os_00778", "os.html#SWS_Os_00778"),
    "ObjectTypeType": ("Os", "SWS_Os_00779", "os.html#SWS_Os_00779"),
    "MemoryStartAddressType": ("Os", "SWS_Os_00780", "os.html#SWS_Os_00780"),
    "MemorySizeType": ("Os", "SWS_Os_00781", "os.html#SWS_Os_00781"),
    "ISRType": ("Os", "SWS_Os_00782", "os.html#SWS_Os_00782"),
}

CLASSIC_TYPE_REGISTRY: Dict[str, ClassicTypeEntry] = {}


def register_type(
    name: str,
    sws_id: str,
    module: str,
    cluster: str = "",
    category: str = "bsw",
    url: str = "",
    desc: str = "",
    type_kind: str = "type",
) -> ClassicTypeEntry:
    """Register or update an AUTOSAR Classic type in the global registry."""
    entry = ClassicTypeEntry(
        name=name,
        sws_id=sws_id,
        module=module,
        cluster=cluster,
        category=category,
        url=url,
        desc=desc,
        type_kind=type_kind,
    )
    CLASSIC_TYPE_REGISTRY[name] = entry
    return entry


def get_type(name: str) -> Optional[ClassicTypeEntry]:
    """Retrieve a registered type by its identifier."""
    return CLASSIC_TYPE_REGISTRY.get(name)


def load_types_from_records(records_dir: Path = RECORDS_DIR) -> int:
    """Scan existing CP_*.json records and register any types found."""
    if not records_dir.is_dir():
        return 0
    added = 0
    heading_to_mod = {}
    for cname, cinfo in CLUSTER_MAP.items():
        for mname, minfo in cinfo["modules"].items():
            heading_to_mod[minfo["heading"]] = (mname, cname)

    for rec_file in records_dir.glob("CP_*.json"):
        try:
            with open(rec_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        cur_mod = ""
        cur_cluster = rec_file.stem.replace("CP_", "")
        for b in data.get("blocks", []):
            h = b.get("html", "")
            for heading, (mname, cname) in heading_to_mod.items():
                if heading in h:
                    cur_mod = mname
                    cur_cluster = cname
                    break
            m_rec = re.search(r"<h3 class=\"recname\"[^>]*><span class=\"kind\">type</span>\s+([A-Za-z0-9_<>]+)\s+<span class=\"sws\">\[([A-Za-z0-9_]+)\]</span>", h)
            if m_rec:
                tname, sws_id = m_rec.group(1), m_rec.group(2)
                if tname not in CLASSIC_TYPE_REGISTRY:
                    mod = cur_mod
                    if not mod or mod.upper() == cur_cluster:
                        if "_" in tname:
                            mod = tname.split("_")[0]
                        else:
                            mod = "Os" if cur_cluster == "OS" else cur_cluster
                    register_type(tname, sws_id, mod, cluster=cur_cluster, category="bsw")
                    added += 1
    return added


def init_type_registry() -> int:
    """Populate CLASSIC_TYPE_REGISTRY with standard platform types and BSW module types."""
    # 1. Standard Platform Types
    for name, (module, sws_id, url) in STANDARD_PLATFORM_TYPES.items():
        register_type(name, sws_id, module, category="standard_platform", url=url)

    # 2. Try loading full fixture if available
    fixture_path = _TOOLS_DIR / "fixtures" / "classic_types.json"
    if fixture_path.is_file():
        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for tname, info in data.items():
                if tname not in CLASSIC_TYPE_REGISTRY:
                    mod, sws_id, cluster = info[0], info[1], info[2]
                    register_type(tname, sws_id, mod, cluster=cluster, category="bsw")
        except Exception as exc:
            LOG.debug("Could not read %s: %s", fixture_path, exc)

    # 3. Fallback: scan RECORDS_DIR if present
    if RECORDS_DIR.is_dir():
        load_types_from_records(RECORDS_DIR)

    return len(CLASSIC_TYPE_REGISTRY)


# Initialize global registry upon module import
init_type_registry()


def link_syntax_types(syntax_str: str, current_module: str = "") -> str:
    """Tokenize a C function signature or parameter string and replace AUTOSAR types with hyperlinks.

    - Types of the same module: <a class="vis-app" href="#{sws_id}">{type_name}</a>
    - Types of other modules: <a class="vis-app" href="{module_url}#{sws_id}">{type_name}</a>
    - Standard Platform Types: <a class="vis-app" href="{std_url}">{type_name}</a> (or same module anchor)
    """
    if not syntax_str:
        return ""

    s = syntax_str

    # Normalize split type names like 'Std_Return Type' -> 'Std_ReturnType' or 'Can_Config Type' -> 'Can_ConfigType'
    s = re.sub(r"([A-Za-z0-9]+)_\s+([A-Za-z0-9]+)", r"\1_\2", s)
    s = re.sub(r"(?<=[A-Za-z0-9_])\s+(Type|Ptr|Info|Mode|Id|StateType)\b", r"\1", s)

    # Determine current module if not supplied
    curr_mod = (current_module or "").strip()
    # Find function name if present (identifier directly preceding opening '(')
    func_name = ""
    m_fn = re.search(r"(?:^|[\s*&])(<[A-Za-z0-9_]+>|[A-Za-z_][A-Za-z0-9_]*)\s*\(", s)
    if m_fn:
        func_name = m_fn.group(1)
        if not curr_mod:
            # Infer from function name prefix: CanIf_Init -> CanIf
            clean_fn = func_name.strip("<>")
            if "_" in clean_fn:
                cand = clean_fn.split("_")[0]
                curr_mod = cand

    curr_mod_lower = curr_mod.lower() if curr_mod else ""

    # Tokenize by HTML tags, HTML entities, and identifiers
    tokens = re.split(r"(<[^>]+>|&[a-zA-Z0-9#]+;|\b[A-Za-z_][A-Za-z0-9_]*\b)", s)
    out = []
    for token in tokens:
        if not token:
            continue
        # Preserve HTML tags and entities as-is
        if token.startswith("<") and token.endswith(">") and re.match(r"^</?[a-zA-Z][^>]*>$", token):
            out.append(token)
            continue
        if token.startswith("&") and token.endswith(";"):
            out.append(token)
            continue

        # Do not link the function name itself
        if func_name and token == func_name:
            out.append(token)
            continue

        # Check if token is in the type registry
        entry = CLASSIC_TYPE_REGISTRY.get(token)
        if entry:
            if entry.category == "standard_platform":
                if curr_mod_lower and entry.module.lower() == curr_mod_lower:
                    href = f"#{entry.sws_id}"
                else:
                    href = entry.url
            else:
                # BSW module type
                if curr_mod_lower and entry.module.lower() == curr_mod_lower:
                    href = f"#{entry.sws_id}"
                else:
                    mod_page = MODULE_TO_PAGE.get(entry.module.lower(), f"{entry.module.lower()}.html")
                    href = f"{mod_page}#{entry.sws_id}"
            out.append(f'<a class="vis-app" href="{href}">{token}</a>')
        else:
            out.append(token)

    return "".join(out)


def format_parameter_blocks(item: Dict[str, Any], current_module: str = "") -> List[Dict[str, Any]]:
    """Format parameter tables (in, out, return value) for an API function with linked types."""
    blocks: List[Dict[str, Any]] = []
    if not current_module:
        current_module = item.get("cluster_module") or item.get("module") or ""
        if not current_module and "_" in item.get("name", ""):
            clean_name = item["name"].strip("<>")
            if "_" in clean_name:
                current_module = clean_name.split("_")[0]

    params_in = item.get("params_in", "").strip()
    if params_in and params_in.lower() != "none":
        linked_in = link_syntax_types(params_in, current_module)
        blocks.append({
            "t": "html",
            "html": f'<h4>Parameter (in)</h4><table class="params"><tr><td class="mono">{linked_in}</td></tr></table>',
            "tail": "\n"
        })

    params_out = item.get("params_out", "").strip()
    if params_out and params_out.lower() != "none":
        linked_out = link_syntax_types(params_out, current_module)
        blocks.append({
            "t": "html",
            "html": f'<h4>Parameter (out)</h4><table class="params"><tr><td class="mono">{linked_out}</td></tr></table>',
            "tail": "\n"
        })

    ret_val = item.get("return_value", "").strip()
    if ret_val and ret_val.lower() != "none":
        linked_ret = link_syntax_types(ret_val, current_module)
        blocks.append({
            "t": "html",
            "html": f'<h4>Rückgabewert</h4><table class="params"><tr><td class="mono">{linked_ret}</td></tr></table>',
            "tail": "\n"
        })

    return blocks


def link_parameter_table(html_str: str, current_module: str = "") -> str:
    """Apply type linking to text content within table cells or HTML snippets."""
    if not html_str:
        return ""
    return link_syntax_types(html_str, current_module)



FOOTER_PATTERNS = [
    re.compile(r"\b\d+\s+of\s+\d+\b.*", re.I),
    re.compile(r"Document\s+ID\s+\d+:.*", re.I),
    re.compile(r"Specification\s+of\s+.*", re.I),
    re.compile(r"AUTOSAR\s+CP\s+.*", re.I),
]


def clean_ident(s: str) -> str:
    """Extract a clean C identifier from a cell, joining split words and ignoring footers/footnotes."""
    if not s:
        return ""
    words = []
    for line in s.splitlines():
        line = line.strip()
        if not line or any(pat.search(line) for pat in FOOTER_PATTERNS):
            continue
        if line.lower() in ("autosar", "cp", "document", "id", "document id", "specification", "of"):
            continue
        if line.startswith("AUTOSAR_SWS_"):
            continue
        if re.match(r"^R\d+(?:-\d+)?$", line, re.I):
            continue
        if re.match(r"^\d+\s*(?:of|-)?\s*\d*$", line, re.I):
            continue
        line = re.sub(r"\.c\(\).*", "", line).strip()
        for w in line.split():
            # Stop if we hit a section header number like 8.1.3
            if re.match(r"^\d+(?:\.\d+)+$", w):
                break
            if re.match(r"^[A-Za-z0-9_<>]+$", w):
                words.append(w)
    ident = "".join(words)
    # Strip trailing attached footnote digit if present (e.g. Mode5 -> Mode)
    if re.search(r"[a-z][A-Z][a-z]+\d$", ident):
        ident = ident[:-1]
    return ident


def clean_type_name(s: str) -> str:
    """Extract a clean type or structure identifier, cutting off table header keywords and footers."""
    if not s:
        return ""
    lines = []
    for line in s.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(pat.search(line) for pat in FOOTER_PATTERNS):
            continue
        if re.match(r"^(?:AUTOSAR|CP|Specification|Document\s*ID|R\d+(?:-\d+)?|\d+\s*of\s*\d+|\d+of\d+.*|:?\s*AUTOSAR_SWS_.*)$", line, re.I):
            continue
        # Stop at table header row keywords
        if re.match(r"^(?:Kind|Structure|Enumeration|Derived|Elements|Comment|Basetype|Range|Variation|Description|Available)(?:\b|[:\s]|$)", line, re.I):
            break
        for w in line.split():
            if re.match(r"^\d+(?:\.\d+)+$", w):
                break
            if re.match(r"^[A-Za-z0-9_<>{}-]+$", w):
                lines.append(w)

    ident = "".join(lines)
    # Strip trailing footnote digit if present (e.g. Type5 -> Type)
    if re.search(r"[a-z][A-Z][a-z]+\d$", ident):
        ident = ident[:-1]

    # If it ends with or contains 'Type', capture clean prefix
    m_type = re.match(r"^([A-Za-z_][A-Za-z0-9_]*?Type)(?:Kind|Structure|Enumeration|Derived|Elements|Comment|Pointer|Range|Variation|Description|[A-Z0-9_-]|$)", ident)
    if m_type:
        return m_type.group(1)

    if ident.endswith("Type") or ident.endswith("Type}"):
        return ident

    # If not ending in Type, cut before table header keywords
    m2 = re.match(r"^(.*?)(?:Kind|Structure|Enumeration|Derived|Elements|Comment|Variation|Description).*", ident)
    if m2 and m2.group(1):
        return m2.group(1)

    return ident


def clean_syntax(s: str) -> str:
    """Format and normalize multi-line C function syntax, removing embedded page headers and fixing split tokens."""
    if not s:
        return ""
    cleaned_lines = []
    for line in s.splitlines():
        line = line.strip()
        if not line or any(pat.search(line) for pat in FOOTER_PATTERNS):
            continue
        if re.match(r"^\d+$", line):
            continue
        cleaned_lines.append(line)

    s = " ".join(cleaned_lines)
    s = re.sub(r"\s+", " ", s).strip()

    # Rejoin underscore splits: e.g. "Std_ Return Type" -> "Std_ReturnType", "Fr Tp_Init" -> "FrTp_Init"
    s = re.sub(r"([A-Za-z0-9])\s+_\s*([A-Za-z0-9])", r"\1_\2", s)
    s = re.sub(r"([A-Za-z0-9])\s+_", r"\1_", s)
    s = re.sub(r"_\s+([A-Za-z0-9])", r"_\1", s)
    s = re.sub(r"(?<=[A-Za-z0-9_])\s+(Type|Ptr|Info|Mode|Id|StateType)\b", r"\1", s)

    # Rejoin module splits: e.g. Fr Tp -> FrTp, Lin If -> LinIf, Can If -> CanIf, Com M -> ComM
    for mod_p, mod_r in [
        (r"\bFr\s+Tp\b", "FrTp"), (r"\bLin\s+If\b", "LinIf"), (r"\bCan\s+If\b", "CanIf"),
        (r"\bCan\s+Tp\b", "CanTp"), (r"\bCan\s+SM\b", "CanSM"), (r"\bCan\s+S\s+M\b", "CanSM"),
        (r"\bFr\s+SM\b", "FrSM"), (r"\bLin\s+SM\b", "LinSM"), (r"\bCom\s+M\b", "ComM"),
        (r"\bBsw\s+M\b", "BswM"), (r"\bWdg\s+M\b", "WdgM"), (r"\bWdg\s+If\b", "WdgIf"),
        (r"\bCry\s+If\b", "CryIf"), (r"\bMem\s+If\b", "MemIf"), (r"\bEth\s+If\b", "EthIf"),
        (r"\bEth\s+SM\b", "EthSM"), (r"\bLin\s+Trcv\b", "LinTrcv"), (r"\bCan\s+Trcv\b", "CanTrcv"),
        (r"\bFr\s+Trcv\b", "FrTrcv"), (r"\bEth\s+Trcv\b", "EthTrcv"), (r"\bFr\s+Ar\s+Tp\b", "FrArTp"),
        (r"\bCor\s+Tst\b", "CorTst"), (r"\bRam\s+Tst\b", "RamTst"),
    ]:
        s = re.sub(mod_p, mod_r, s)

    # Rejoin common split fragments in AUTOSAR Classic types and parameters
    for prefix, suffix in [
        ("Return", "Type"), ("Config", "Ptr"), ("Config", "Type"),
        ("Module", "Id"), ("Instance", "Id"), ("Api", "Id"), ("Error", "Id"),
        ("Version", "Info"), ("Info", "Ptr"), ("Controller", "Id"),
        ("Transceiver", "Id"), ("State", "Type"), ("Pdu", "Id"),
        ("Wakeup", "Mode"), ("Wakeup", "Source"), ("Report", "Error"),
        ("Report", "Runtime"), ("Runtime", "Error"), ("Report", "Transient"),
        ("Transient", "Fault"), ("User_", "Error"), ("Error_", "Hooks"),
        ("Get", "Version"), ("Version", "Info"), ("Get", "VersionInfo"),
        ("Rx", "Indication"), ("Tx", "Confirmation"), ("Main", "Function"),
        ("Cancel", "Transmit"), ("Change", "Parameter"), ("Cancel", "Receive"),
        ("Trigger", "Transmit"), ("Setup", "ResultBuffer"), ("Setup", "Result Buffer"),
        ("Rx", "PduId"), ("Tx", "PduId"), ("Data", "Buffer"),
    ]:
        s = re.sub(rf"\b{prefix}\s+{suffix}\b", f"{prefix}{suffix}", s)

    s = re.sub(r"\s*\(\s*", "(", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*\*\s*", "* ", s)
    s = re.sub(r"\s+;", ";", s)
    if s and not s.endswith(";"):
        s += ";"
    return s


def clean_text(s: str) -> str:
    """Normalize extracted prose description and strip footer artifacts."""
    if not s:
        return ""
    cleaned_lines = []
    for line in s.splitlines():
        line = line.strip()
        if not line or any(pat.search(line) for pat in FOOTER_PATTERNS):
            continue
        if re.match(r"^\d+$", line):
            continue
        cleaned_lines.append(line)

    s = " ".join(cleaned_lines)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(?:–|—|-)\s*", "", s)
    return s


def extract_functions_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """Linear O(N) line-by-line extractor for AUTOSAR Classic SWS Chapter 8 function and type tables."""
    if not pdf_path.is_file():
        LOG.debug("PDF file does not exist: %s", pdf_path)
        return []

    try:
        pages = spec_scrape.pdf_pages(pdf_path, backend="builtin")
    except Exception as exc:
        LOG.warning("Failed to read pages from %s: %s", pdf_path, exc)
        return []

    records = []
    seen_ids = set()

    # Build flat line array with page tracking to seamlessly cross page boundaries
    all_lines: List[Tuple[int, str]] = []
    for pno, page_text in enumerate(pages):
        for line in page_text.splitlines():
            l = line.strip()
            if l:
                all_lines.append((pno + 1, l))

    i, n = 0, len(all_lines)
    while i < n:
        pno, line = all_lines[i]
        m_id = re.search(r"\[(SWS_[A-Za-z0-9]+_\d{4,6})\]", line)
        if m_id:
            sws_id = m_id.group(1)
            props: Dict[str, str] = {}
            cur_key: Optional[str] = None
            buf: List[str] = []

            j = i + 1
            while j < min(n, i + 120):
                _p, l = all_lines[j]
                if j > i + 1 and re.search(r"\[SWS_[A-Za-z0-9]+_\d{4,6}\]", l):
                    break

                matched_key = None
                for k in TABLE_KEYS:
                    if l == k or l.startswith(k + ":") or l.startswith(k + " "):
                        matched_key = k
                        break

                if not matched_key:
                    if l in ("Available", "Available via") and j + 1 < min(n, i + 120) and all_lines[j + 1][1].strip() == "via":
                        matched_key = "Available via"
                        j += 1
                    elif l == "Derived" and j + 1 < min(n, i + 120) and all_lines[j + 1][1].strip().lower() == "from":
                        matched_key = "Derived from"
                        j += 1
                    elif l in ("Service", "Service Nam") and j + 1 < min(n, i + 120) and (all_lines[j + 1][1].strip().startswith("Name") or all_lines[j + 1][1].strip() == "e"):
                        matched_key = "Service Name"
                        j += 1

                if matched_key:
                    if cur_key:
                        props[cur_key] = "\n".join(buf)
                    cur_key = matched_key
                    remainder = l[len(matched_key):].lstrip(": ")
                    buf = [remainder] if remainder else []
                elif cur_key:
                    if l.startswith("⌋") or l.startswith("c (") or l.startswith("c("):
                        props[cur_key] = "\n".join(buf)
                        cur_key = None
                        break
                    buf.append(l)
                j += 1

            if cur_key:
                props[cur_key] = "\n".join(buf)

            name_raw = props.get("Service Name") or props.get("Name")
            syntax_raw = props.get("Syntax")
            kind_raw = props.get("Kind")
            desc = clean_text(props.get("Description", ""))
            header = clean_ident(props.get("Available via", ""))

            has_func_syntax = bool(syntax_raw and "(" in syntax_raw and ")" in syntax_raw)
            raw_kind = kind_raw.strip().split()[0] if kind_raw and kind_raw.strip().split() else ""
            raw_lower = (kind_raw or "").strip().lower()
            is_type_kind = any(k in raw_lower for k in ("type", "struct", "enum", "pointer", "bitfield", "array", "mode", "const"))

            if sws_id not in seen_ids:
                if has_func_syntax and not is_type_kind:
                    # Clean function entry (Kapitel 8.3/8.4/8.5)
                    syntax = clean_syntax(syntax_raw or "")
                    func_name = ""
                    if name_raw:
                        func_name = clean_ident(name_raw)
                    if not func_name and syntax:
                        m_name = re.search(r"(?:^|\s)(<?[A-Za-z0-9_]+>?)\s*\(", syntax)
                        if m_name:
                            func_name = m_name.group(1)

                    if func_name and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", func_name) or re.match(r"^<[A-Za-z0-9_]+>$", func_name)):
                        seen_ids.add(sws_id)
                        records.append({
                            "id": sws_id,
                            "name": func_name,
                            "kind": "function",
                            "syntax": syntax,
                            "desc": desc or f"Service {func_name}.",
                            "header": header,
                            "service_id": clean_text(props.get("Service ID [hex]") or props.get("Service ID", "")),
                            "sync_async": clean_text(props.get("Sync/Async", "")),
                            "reentrancy": clean_text(props.get("Reentrancy", "")),
                            "params_in": clean_text(props.get("Parameters (in)", "")),
                            "params_out": clean_text(props.get("Parameters (out)", "")),
                            "return_value": clean_text(props.get("Return value", "")),
                            "page": pno,
                        })

                elif is_type_kind or (not has_func_syntax and not props.get("Service Name") and name_raw and clean_type_name(name_raw).endswith("Type")):
                    # Clean datatype / structure entry (Kapitel 8.2)
                    t_name = clean_type_name(name_raw or "")
                    if sws_id == "SWS_Std_00006":
                        t_name = "E_OK / E_NOT_OK"
                    elif sws_id == "SWS_Std_00007":
                        t_name = "STD_HIGH / STD_LOW"
                    elif sws_id == "SWS_Std_00010":
                        t_name = "STD_ON / STD_OFF"
                    elif sws_id == "SWS_Std_00013":
                        t_name = "STD_ACTIVE / STD_IDLE"
                    elif sws_id == "SWS_Std_91003":
                        t_name = "Std_ExtractProtocolHeaderFieldsType"

                    if t_name and not t_name.startswith("=") and not t_name.startswith("{"):
                        if re.match(r"^[A-Za-z_][A-Za-z0-9_ /]*$", t_name) or re.match(r"^<[A-Za-z0-9_]+>$", t_name):
                            seen_ids.add(sws_id)
                            t_kind = raw_kind or "Type"
                            t_syntax = KNOWN_TYPE_SYNTAX.get(t_name, clean_syntax(syntax_raw or ""))
                            records.append({
                                "id": sws_id,
                                "name": t_name,
                                "kind": "type",
                                "syntax": t_syntax,
                                "desc": desc or f"Type {t_name}.",
                                "header": header,
                                "type_kind": t_kind,
                                "page": pno,
                            })

            i = j - 1
        i += 1

    if pdf_path.name == "AUTOSAR_SWS_OS.pdf":
        for os_type in OS_BASE_TYPES:
            if os_type["id"] not in seen_ids:
                seen_ids.add(os_type["id"])
                records.append(dict(os_type))

    return records


def format_function_blocks(
    item: Dict[str, Any],
    current_module: str = "",
    include_params: bool = False,
    pdf_doc: str = "",
    root_rel: str = "../../"
) -> List[Dict[str, Any]]:
    """Format one function or type definition into the JSON block structure required by autodocs."""
    sws_id = item["id"]
    name = item["name"]
    kind = item.get("kind", "function")
    desc = item.get("desc") or (f"Service {name}." if kind != "type" else f"Type {name}.")

    if "AUTOSAR" in name and not name.startswith("AUTOSAR"):
        name = re.sub(r"AUTOSAR.*$", "", name).strip()

    if not current_module:
        current_module = item.get("cluster_module") or item.get("module") or ""
        if not current_module and "_" in name:
            clean_name = name.strip("<>")
            if "_" in clean_name:
                current_module = clean_name.split("_")[0]

    sws_link = f'<a href="{root_rel}versions.html?id={sws_id}" title="Requirement im Versions- &amp; Revisions-Explorer anzeigen">[{sws_id}]</a>'
    pdf_link = ""
    if pdf_doc:
        page = item.get("page")
        if page:
            p_title = f"Spezifikations-PDF im Original öffnen: {pdf_doc} (Anker: #{sws_id}, S. {page})"
        else:
            p_title = f"Spezifikations-PDF im Original öffnen: {pdf_doc} (Anker: #{sws_id})"
        pdf_url = f"https://www.autosar.org/fileadmin/standards/R20-11/CP/{pdf_doc}#nameddest={sws_id}"
        pdf_link = f' <a href="{pdf_url}" target="_blank" rel="noopener noreferrer" class="sws-pdf-link" title="{p_title}">📄 PDF</a>'

    blocks = [
        {
            "t": "html",
            "html": f'<h3 class="recname" id="{sws_id}"><span class="kind">{kind}</span> {name} <span class="sws">{sws_link}</span>{pdf_link}</h3>',
            "tail": "\n"
        }
    ]
    if item.get("syntax"):
        syn = item["syntax"]
        if kind == "function":
            m_paren = re.search(r"^(.*?\(.*?\))(?:[^;]*;?)?.*$", syn, re.DOTALL)
            if m_paren:
                syn = m_paren.group(1).strip() + ";"
        linked_syntax = link_syntax_types(syn, current_module)
        blocks.append({
            "t": "html",
            "html": f'<pre class="syntax">{linked_syntax}</pre>',
            "tail": "\n"
        })
    blocks.append({
        "t": "html",
        "html": f'<div class="desc"><p>{desc}</p></div>',
        "tail": "\n"
    })

    if include_params and kind == "function":
        blocks.extend(format_parameter_blocks(item, current_module))

    return blocks


def rebuild_cluster_record(cluster_name: str, cache_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Rebuild or expand a CP_*.json record file from extracted PDF functions and types."""
    meta = CLUSTER_MAP.get(cluster_name)
    if not meta:
        raise ValueError(f"Unknown cluster: {cluster_name}. Choices: {list(CLUSTER_MAP.keys())}")

    record_file = RECORDS_DIR / meta["record"]
    existing_data: Dict[str, Any] = {}
    if record_file.is_file():
        try:
            with open(record_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as exc:
            LOG.warning("Could not read existing %s: %s", record_file, exc)

    module_id = meta["record"].replace(".json", "")
    new_record = {
        "module": module_id,
        "platform": "classic",
        "id": module_id,
        "attrs": [["class", "rec"], ["id", module_id]],
        "lead": "\n",
        "blocks": []
    }

    total_funcs = 0
    total_types = 0
    for mod_key, mod_info in meta["modules"].items():
        pdf_path = cache_dir / mod_info["pdf"]
        items = extract_functions_from_pdf(pdf_path)
        functions = [it for it in items if it.get("kind") == "function"]
        types = [it for it in items if it.get("kind") == "type"]
        total_funcs += len(functions)
        total_types += len(types)
        LOG.info("[%s] %s (%s): %d functions, %d types extracted", cluster_name, mod_key, mod_info["pdf"], len(functions), len(types))

        # Add section heading block
        new_record["blocks"].append({
            "t": "html",
            "html": f"<h2>{mod_info['heading']}</h2><p class=\"lead\">{mod_info['lead']}</p>",
            "tail": "\n"
        })

        if items:
            # Order: functions first, then datatypes
            for f in functions:
                new_record["blocks"].extend(format_function_blocks(f, current_module=mod_key))
            for t in types:
                new_record["blocks"].extend(format_function_blocks(t, current_module=mod_key))
        else:
            # Fallback: keep existing functions/types for this module if PDF was not found/extracted
            existing_blocks = existing_data.get("blocks", [])
            in_section = False
            for b in existing_blocks:
                h = b.get("html", "")
                if mod_info["heading"] in h:
                    in_section = True
                    continue
                elif in_section and "<h2>" in h:
                    break
                if in_section:
                    new_record["blocks"].append(b)

    if not dry_run:
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(new_record, f, indent=1, ensure_ascii=False)
            f.write("\n")
        LOG.info("Wrote %s with %d functions, %d types (%d total)", record_file, total_funcs, total_types, total_funcs + total_types)

    return {
        "cluster": cluster_name,
        "record_file": str(record_file),
        "functions_count": total_funcs,
        "types_count": total_types,
        "total_count": total_funcs + total_types
    }


def rebuild_module_record(mod_key: str, cache_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Rebuild a single module record under _src/spec/records/classic/modules/<Mod>.json."""
    target_cluster = None
    target_info = None
    for cname, meta in CLUSTER_MAP.items():
        if mod_key in meta["modules"]:
            target_cluster = cname
            target_info = meta["modules"][mod_key]
            break
    if not target_info:
        raise ValueError(f"Unknown module: {mod_key}")

    MODULES_RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = MODULES_RECORDS_DIR / f"{mod_key}.json"

    # Attempt PDF extraction
    pdf_path = cache_dir / target_info["pdf"]
    items = extract_functions_from_pdf(pdf_path) if pdf_path.is_file() else []
    functions = [it for it in items if it.get("kind") == "function"]
    types = [it for it in items if it.get("kind") == "type"]

    item_blocks = []
    overview_blocks = []
    if items:
        if functions:
            func_items = []
            for f in functions:
                sws_id = f["id"]
                name = f["name"]
                if "AUTOSAR" in name and not name.startswith("AUTOSAR"):
                    name = re.sub(r"AUTOSAR.*$", "", name).strip()
                syntax = f.get("syntax", "")
                m_paren = re.search(r"^(.*?\(.*?\))(?:[^;]*;?)?.*$", syntax, re.DOTALL)
                clean_syn = m_paren.group(1).strip() + ";" if m_paren else (syntax + ";" if not syntax.endswith(";") else syntax)
                idx_p = clean_syn.find("(")
                if idx_p != -1:
                    prefix = clean_syn[:idx_p].strip()
                    params = clean_syn[idx_p:].strip()
                    letters = list(re.escape(name))
                    m_fn = re.search(r"\s*".join(letters), prefix, re.IGNORECASE)
                    if m_fn:
                        ret_type = prefix[:m_fn.start()].strip()
                        fn_part = f'<a class="fn" href="#{sws_id}">{name}</a>'
                        sig = f"{ret_type} {fn_part} {params}" if ret_type else f"{fn_part} {params}"
                        sig = " ".join(sig.split())
                    else:
                        sig = f'<a class="fn" href="#{sws_id}">{name}</a> {params}'
                else:
                    sig = f'<a class="fn" href="#{sws_id}">{name}</a>;'
                desc = f.get("desc") or f"Service {name}."
                txt = re.sub(r"<[^>]+>", "", desc).strip()
                if "." in txt:
                    txt = txt.split(".")[0].strip() + "."
                if len(txt) > 130:
                    txt = txt[:127].rsplit(" ", 1)[0] + "..."
                func_items.append(f'  <li><code class="sig">{sig}</code> <span class="dim">{txt}</span></li>')
            overview_blocks.append({
                "t": "html",
                "html": "<h3>Funktionen — Übersicht</h3>\n<ul class=\"mlist\">\n" + "\n".join(func_items) + "\n</ul>",
                "tail": "\n"
            })
        if types:
            type_items = []
            for t in types:
                sws_id = t["id"]
                name = t["name"]
                sig = f'<a class="fn" href="#{sws_id}">{name}</a>'
                desc = t.get("desc") or f"Type {name}."
                txt = re.sub(r"<[^>]+>", "", desc).strip()
                if "." in txt:
                    txt = txt.split(".")[0].strip() + "."
                if len(txt) > 130:
                    txt = txt[:127].rsplit(" ", 1)[0] + "..."
                type_items.append(f'  <li><code class="sig">{sig}</code> <span class="dim">{txt}</span></li>')
            overview_blocks.append({
                "t": "html",
                "html": "<h3>Typen — Übersicht</h3>\n<ul class=\"mlist\">\n" + "\n".join(type_items) + "\n</ul>",
                "tail": "\n"
            })
        if functions or types:
            div_title = "Funktionen &amp; Typen — Detailansicht" if (functions and types) else ("Typen — Detailansicht" if types else "Funktionen — Detailansicht")
            overview_blocks.append({
                "t": "html",
                "html": f'<h2 class="sect">{div_title}</h2>',
                "tail": "\n"
            })

        for f in functions:
            item_blocks.extend(format_function_blocks(f, current_module=mod_key, pdf_doc=target_info["pdf"]))
        for t in types:
            item_blocks.extend(format_function_blocks(t, current_module=mod_key, pdf_doc=target_info["pdf"]))
    else:
        # Fallback: extract existing blocks from cluster record CP_<cluster>.json
        cluster_file = RECORDS_DIR / CLUSTER_MAP[target_cluster]["record"]
        if cluster_file.is_file():
            try:
                with open(cluster_file, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                in_section = False
                for b in cdata.get("blocks", []):
                    h = b.get("html", "")
                    if target_info["heading"] in h:
                        in_section = True
                        continue
                    elif in_section and "<h2>" in h:
                        break
                    if in_section:
                        item_blocks.append(b)
            except Exception as exc:
                LOG.warning("Could not read fallback from %s: %s", cluster_file, exc)

    module_record = {
        "module": mod_key,
        "platform": "classic",
        "id": f"CP_MOD_{mod_key}",
        "attrs": [["class", "rec"], ["id", f"CP_MOD_{mod_key}"]],
        "lead": "\n",
        "blocks": [
            {
                "t": "html",
                "html": f"<h2>{target_info['heading']}</h2><p class=\"lead\">{target_info['lead']}</p>",
                "tail": "\n"
            }
        ] + overview_blocks + item_blocks
    }

    funcs_count = sum(1 for b in item_blocks if "<h3 class=\"recname\"" in b.get("html", "") and '<span class="kind">function</span>' in b.get("html", ""))
    types_count = sum(1 for b in item_blocks if "<h3 class=\"recname\"" in b.get("html", "") and '<span class="kind">type</span>' in b.get("html", ""))
    total_count = funcs_count + types_count

    if not dry_run:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(module_record, f, indent=1, ensure_ascii=False)
            f.write("\n")
        LOG.info("Wrote module record %s with %d functions, %d types (%d total)", out_file, funcs_count, types_count, total_count)

    return {
        "module": mod_key,
        "cluster": target_cluster,
        "record_file": str(out_file),
        "functions_count": funcs_count,
        "types_count": types_count,
        "total_count": total_count
    }


def rebuild_all_module_records(cache_dir: Path, dry_run: bool = False) -> List[Dict[str, Any]]:
    """Rebuild all module records under _src/spec/records/classic/modules/."""
    results = []
    for cname, meta in CLUSTER_MAP.items():
        for mkey in meta["modules"]:
            res = rebuild_module_record(mkey, cache_dir, dry_run=dry_run)
            results.append(res)
    return results


def generate_module_page(mod_key: str, dry_run: bool = False) -> str:
    """Generate page model under _src/sources/pages/classic/modules/<mod_lower>.json."""
    target_cluster = None
    target_info = None
    for cname, meta in CLUSTER_MAP.items():
        if mod_key in meta["modules"]:
            target_cluster = cname
            target_info = meta["modules"][mod_key]
            break
    if not target_info:
        raise ValueError(f"Unknown module: {mod_key}")

    MODULES_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    mod_lower = mod_key.lower()
    page_file = MODULES_PAGES_DIR / f"{mod_lower}.json"

    cluster_file = CLUSTER_PAGE_MAP[target_cluster]
    cluster_title = CLUSTER_TITLE_MAP[target_cluster]
    mod_name = target_info.get("name", mod_key)
    bsw_id = target_info.get("bsw_id", "-")
    header = target_info.get("header", f"{mod_key}.h")
    pdf = target_info.get("pdf", "")

    # Read existing page to preserve any AI fold
    existing_folds = []
    if page_file.is_file():
        try:
            with open(page_file, "r", encoding="utf-8") as f:
                cur_page = json.load(f)
            for b in cur_page.get("main", []):
                if b.get("t") == "fold":
                    existing_folds.append(b)
        except Exception:
            pass

    page_data = {
        "file": f"classic/modules/{mod_lower}.html",
        "title": f"AUTOSAR Classic {mod_name} ({mod_key})",
        "body_class": "vis-app",
        "nav_html": f"<a href=\"../../index.html\">Start</a> \u203a <a href=\"../index.html\">AUTOSAR Classic</a> \u203a <a href=\"../{cluster_file}\">{cluster_title}</a> \u203a <span>{mod_key}</span>",
        "footer": "extracted",
        "main_lead": "",
        "main": [
            {
                "t": "html",
                "html": f"<h1>{target_info['heading']}</h1>",
                "tail": "\n"
            },
            {
                "t": "html",
                "html": (
                    f"<div class=\"module-meta\">\n"
                    f"<table class=\"props\">\n"
                    f"<tbody>\n"
                    f"<tr><th>Modul</th><td><strong>{mod_key}</strong> ({mod_name})</td></tr>\n"
                    f"<tr><th>BSW-Modul-ID</th><td><code>{bsw_id}</code></td></tr>\n"
                    f"<tr><th>Standard-Header</th><td><code>#include &quot;{header}&quot;</code></td></tr>\n"
                    f"<tr><th>SWS-Spezifikation</th><td><a href=\"https://www.autosar.org/fileadmin/standards/R20-11/CP/{pdf}\">{pdf}</a></td></tr>\n"
                    f"<tr><th>Cluster</th><td><a href=\"../{cluster_file}\">{cluster_title}</a></td></tr>\n"
                    f"</tbody>\n"
                    f"</table>\n"
                    f"</div>"
                ),
                "tail": "\n"
            }
        ] + existing_folds + [
            {
                "t": "rec-ref",
                "src": f"spec/records/classic/modules/{mod_key}.json",
                "tail": "\n"
            }
        ],
        "i18n_complete": True
    }

    if not dry_run:
        with open(page_file, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=1, ensure_ascii=False)
            f.write("\n")
        LOG.info("Wrote module page %s", page_file)

    return str(page_file)


def generate_all_module_pages(dry_run: bool = False) -> List[str]:
    """Generate all 41 module pages under _src/sources/pages/classic/modules/."""
    written = []
    for cname, meta in CLUSTER_MAP.items():
        for mkey in meta["modules"]:
            p = generate_module_page(mkey, dry_run=dry_run)
            written.append(p)
    return written


def generate_cluster_hub_page(cluster_name: str, dry_run: bool = False) -> str:
    """Generate streamlined cluster hub under _src/sources/pages/classic/<cluster_file>.json."""
    meta = CLUSTER_MAP.get(cluster_name)
    if not meta:
        raise ValueError(f"Unknown cluster: {cluster_name}")

    cluster_file = CLUSTER_PAGE_MAP[cluster_name]
    cluster_title = CLUSTER_TITLE_MAP[cluster_name]
    page_path = PAGES_DIR / cluster_file.replace(".html", ".json")

    # Read existing page to preserve any AI fold
    existing_folds = []
    if page_path.is_file():
        try:
            with open(page_path, "r", encoding="utf-8") as f:
                cur_page = json.load(f)
            for b in cur_page.get("main", []):
                if b.get("t") == "fold":
                    existing_folds.append(b)
        except Exception:
            pass

    # Build module cards
    cards_html = ["<h2 class=\"sect\">Module im Cluster</h2>\n<div class=\"cards\">\n"]
    for mkey, minfo in meta["modules"].items():
        m_lower = mkey.lower()
        rec_file = MODULES_RECORDS_DIR / f"{mkey}.json"
        f_count = 0
        t_count = 0
        if rec_file.is_file():
            try:
                with open(rec_file, "r", encoding="utf-8") as rf:
                    rdata = json.load(rf)
                for b in rdata.get("blocks", []):
                    h = b.get("html", "")
                    if "<h3 class=\"recname\"" in h:
                        if '<span class="kind">type</span>' in h:
                            t_count += 1
                        else:
                            f_count += 1
            except Exception:
                pass
        tot = f_count + t_count
        tot_label = f"{tot} APIs ({f_count} Funktionen, {t_count} Typen)" if tot else "API-Referenz"
        bsw_label = f"BSW ID {minfo.get('bsw_id', '-')}"
        hdr_label = f'#include &quot;{minfo.get("header", mkey + ".h")}&quot;'

        cards_html.append(
            f'  <a class="card" href="modules/{m_lower}.html">\n'
            f'    <h3>{minfo["heading"]}</h3>\n'
            f'    <p>{minfo["lead"]}</p>\n'
            f'    <div class="card-meta">\n'
            f'      <span class="chip">{bsw_label}</span>\n'
            f'      <span class="chip">{tot_label}</span>\n'
            f'      <span class="chip"><code>{hdr_label}</code></span>\n'
            f'    </div>\n'
            f'  </a>\n'
        )
    cards_html.append("</div>")

    overview_text = CLUSTER_OVERVIEW_MAP.get(cluster_name, meta["title"])

    main_blocks = [
        {
            "t": "html",
            "html": f"<h1>AUTOSAR Classic {cluster_title}</h1>",
            "tail": "\n"
        }
    ]
    # Add preserved AI folds
    for fold in existing_folds:
        main_blocks.append(fold)

    # Add architecture overview and module cards
    main_blocks.append({
        "t": "html",
        "html": (
            f"<div class=\"cluster-overview\">\n"
            f"<p class=\"lead\">{overview_text}</p>\n"
            f"</div>\n"
            f"{''.join(cards_html)}"
        ),
        "tail": "\n"
    })

    page_data = {
        "file": f"classic/{cluster_file}",
        "title": f"AUTOSAR Classic {cluster_title}",
        "body_class": "vis-app",
        "nav_html": f"<a href=\"../index.html\">Start</a> \u203a <a href=\"index.html\">AUTOSAR Classic</a> \u203a <span>{cluster_title}</span>",
        "footer": "extracted",
        "main_lead": "",
        "main": main_blocks,
        "i18n_complete": True
    }

    if not dry_run:
        with open(page_path, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=1, ensure_ascii=False)
            f.write("\n")
        LOG.info("Wrote cluster hub %s", page_path)

    return str(page_path)


def generate_all_cluster_hubs(dry_run: bool = False) -> List[str]:
    """Generate all 13 streamlined cluster hubs under _src/sources/pages/classic/."""
    written = []
    for cname in CLUSTER_MAP:
        p = generate_cluster_hub_page(cname, dry_run=dry_run)
        written.append(p)
    return written


def check_all_clusters(cache_dir: Path) -> List[Dict[str, Any]]:
    """Audit all clusters: report PDFs present, functions & types extracted vs. in current records."""
    results = []
    for cluster_name, meta in CLUSTER_MAP.items():
        rec_path = RECORDS_DIR / meta["record"]
        current_funcs = 0
        current_types = 0
        if rec_path.is_file():
            try:
                with open(rec_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for b in data.get("blocks", []):
                        html = b.get("html", "")
                        if "<h3 class=\"recname\"" in html:
                            if '<span class="kind">type</span>' in html:
                                current_types += 1
                            else:
                                current_funcs += 1
            except Exception:
                pass

        extracted_funcs = 0
        extracted_types = 0
        modules_info = []
        for mod_key, mod_info in meta["modules"].items():
            pdf_path = cache_dir / mod_info["pdf"]
            pdf_present = pdf_path.is_file()
            items = extract_functions_from_pdf(pdf_path) if pdf_present else []
            f_count = sum(1 for it in items if it.get("kind") == "function")
            t_count = sum(1 for it in items if it.get("kind") == "type")
            extracted_funcs += f_count
            extracted_types += t_count
            modules_info.append({
                "module": mod_key,
                "pdf": mod_info["pdf"],
                "present": pdf_present,
                "functions": f_count,
                "types": t_count,
                "extracted": len(items)
            })

        results.append({
            "cluster": cluster_name,
            "record": meta["record"],
            "current_funcs": current_funcs,
            "current_types": current_types,
            "current_total": current_funcs + current_types,
            "extracted_funcs": extracted_funcs,
            "extracted_types": extracted_types,
            "extracted_total": extracted_funcs + extracted_types,
            "modules": modules_info
        })
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR), help="Path to Classic SWS PDF directory")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="List configured clusters and their SWS PDFs")

    p_extract = sub.add_parser("extract", help="Extract functions and types from a PDF or cluster")
    p_extract.add_argument("--pdf", help="Filename of a specific PDF to parse")
    p_extract.add_argument("--cluster", choices=list(CLUSTER_MAP.keys()), help="Cluster to parse")
    p_extract.add_argument("--json", action="store_true", help="Output JSON instead of summary")

    p_check = sub.add_parser("check", help="Compare current records with PDF cache potential")

    p_rebuild = sub.add_parser("rebuild", help="Rebuild records under _src/spec/records/classic/")
    p_rebuild.add_argument("--cluster", choices=list(CLUSTER_MAP.keys()), help="Specific cluster to rebuild")
    p_rebuild.add_argument("--module", help="Specific module to rebuild")
    p_rebuild.add_argument("--modules", action="store_true", help="Rebuild all module records under _src/spec/records/classic/modules/")
    p_rebuild.add_argument("--all", action="store_true", help="Rebuild all clusters and module records")
    p_rebuild.add_argument("--dry-run", action="store_true", help="Do not write files")

    p_gen = sub.add_parser("generate-pages", help="Generate or update module pages and cluster hubs under _src/sources/pages/classic/")
    p_gen.add_argument("--dry-run", action="store_true", help="Do not write files")

    args = parser.parse_args(argv)
    cache_dir = Path(args.cache_dir)

    if args.cmd == "list":
        print(f"Classic SWS Cache Directory: {cache_dir}")
        for cname, meta in CLUSTER_MAP.items():
            print(f"\nCluster: {cname} ({meta['record']}) — {meta['title']}")
            for mkey, minfo in meta["modules"].items():
                p = cache_dir / minfo["pdf"]
                status = "✓ PRESENT" if p.is_file() else "✗ MISSING"
                print(f"  - {mkey:8s} {minfo['pdf']:45s} [{status}]")
        return 0

    elif args.cmd == "extract":
        if args.pdf:
            pdf_path = cache_dir / args.pdf
            items = extract_functions_from_pdf(pdf_path)
            if args.json:
                print(json.dumps(items, indent=2, ensure_ascii=False))
            else:
                f_count = sum(1 for it in items if it.get("kind") == "function")
                t_count = sum(1 for it in items if it.get("kind") == "type")
                print(f"Extracted {len(items)} items ({f_count} functions, {t_count} types) from {args.pdf}:")
                for it in items:
                    kind = it.get("kind", "function")
                    if kind == "function":
                        print(f"  [{it['id']}] ({kind}) {it['name']} -> {it['syntax']}")
                    else:
                        print(f"  [{it['id']}] ({kind}) {it['name']}")
            return 0
        elif args.cluster:
            meta = CLUSTER_MAP[args.cluster]
            all_items = []
            for mkey, minfo in meta["modules"].items():
                p = cache_dir / minfo["pdf"]
                items = extract_functions_from_pdf(p)
                for it in items:
                    it["cluster_module"] = mkey
                all_items.extend(items)
            if args.json:
                print(json.dumps(all_items, indent=2, ensure_ascii=False))
            else:
                f_count = sum(1 for it in all_items if it.get("kind") == "function")
                t_count = sum(1 for it in all_items if it.get("kind") == "type")
                print(f"Cluster {args.cluster}: Extracted {len(all_items)} items ({f_count} functions, {t_count} types):")
                for it in all_items:
                    kind = it.get("kind", "function")
                    if kind == "function":
                        print(f"  ({it['cluster_module']}) [{it['id']}] ({kind}) {it['name']} -> {it['syntax']}")
                    else:
                        print(f"  ({it['cluster_module']}) [{it['id']}] ({kind}) {it['name']}")
            return 0
        else:
            parser.error("extract requires --pdf or --cluster")

    elif args.cmd == "check":
        results = check_all_clusters(cache_dir)
        hdr = "{:<10} {:<16} {:<12} {:<14} {:<8}".format("Cluster", "Record", "Cur(F/T)", "Ext(F/T)", "Total")
        print(hdr)
        print("-" * len(hdr))
        for r in results:
            cur_ft = f"{r['current_funcs']}/{r['current_types']}"
            ext_ft = f"{r['extracted_funcs']}/{r['extracted_types']}"
            print(f"{r['cluster']:<10} {r['record']:<16} {cur_ft:<12} {ext_ft:<14} {r['extracted_total']:<8}")
        return 0

    elif args.cmd == "rebuild":
        if args.module:
            res = rebuild_module_record(args.module, cache_dir, dry_run=args.dry_run)
            print(f"Module {res['module']}: {res['functions_count']} functions, {res['types_count']} types ({res['total_count']} total) -> {res['record_file']}")
            return 0
        elif args.modules:
            m_results = rebuild_all_module_records(cache_dir, dry_run=args.dry_run)
            hdr = "{:<10} {:<10} {:<12} {:<10} {:<10}".format("Cluster", "Module", "Functions", "Types", "Total")
            print(f"\n{hdr}")
            print("-" * len(hdr))
            for r in m_results:
                print(f"{r['cluster']:<10} {r['module']:<10} {r['functions_count']:<12} {r['types_count']:<10} {r['total_count']:<10}")
            return 0
        elif args.all:
            rebuild_results = []
            for cname in CLUSTER_MAP:
                res = rebuild_cluster_record(cname, cache_dir, dry_run=args.dry_run)
                rebuild_results.append(res)
            m_results = rebuild_all_module_records(cache_dir, dry_run=args.dry_run)
            hdr = "{:<10} {:<12} {:<10} {:<10}".format("Cluster", "Functions", "Types", "Total")
            print(f"\n{hdr}")
            print("-" * len(hdr))
            for r in rebuild_results:
                print(f"{r['cluster']:<10} {r['functions_count']:<12} {r['types_count']:<10} {r['total_count']:<10}")
            print(f"\nRebuilt {len(m_results)} module records under _src/spec/records/classic/modules/.")
            return 0
        elif args.cluster:
            res = rebuild_cluster_record(args.cluster, cache_dir, dry_run=args.dry_run)
            hdr = "{:<10} {:<12} {:<10} {:<10}".format("Cluster", "Functions", "Types", "Total")
            print(f"\n{hdr}")
            print("-" * len(hdr))
            print(f"{res['cluster']:<10} {res['functions_count']:<12} {res['types_count']:<10} {res['total_count']:<10}")
            return 0
        else:
            parser.error("rebuild requires --cluster, --module, --modules, or --all")

    elif args.cmd == "generate-pages":
        m_pages = generate_all_module_pages(dry_run=args.dry_run)
        c_hubs = generate_all_cluster_hubs(dry_run=args.dry_run)
        print(f"Generated {len(m_pages)} module pages under _src/sources/pages/classic/modules/")
        print(f"Generated {len(c_hubs)} cluster hubs under _src/sources/pages/classic/")
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
