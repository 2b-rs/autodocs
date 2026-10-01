# ECU SUP.8 Configuration Management Architecture (Feature 0027-05)

## Purpose
This document establishes the architecture for ECU configuration management in compliance with Automotive SPICE SUP.8. It applies to all ECU process instances, extending the baseline pipeline CM (Feature 0015) to cover specialized ECU assets.

## 1. Managed Items Scope
The CM system must uniquely identify, control, and version the following ECU-specific artifacts:
- Requirements, Architecture, and Design Models.
- Source Code and Generated Code.
- Compiled Binaries and Firmware Images.
- Toolchains, Build Configurations, and Makefiles.
- Calibration Parameters and Variant Data.
- Test Assets (scripts, fixtures) and Test Environments (HIL/SIL setups).
- Supplier Items (e.g., third-party libraries).
- Records and Evidence (stored in the Immutable Evidence Repository).
- Release Packages.

## 2. Baselines and Versioning
- **Controlled Changes:** Every change to a managed item must be authorized and traceable (SUP.10 integration).
- **Baselines:** The system must support the creation of immutable baselines (e.g., pre-test baseline, release baseline). A baseline is a cryptographically secured manifest linking the exact versions of all constituent configuration items.

## 3. Status Accounting & Audits
- **Status Accounting:** The CM system must be able to report the current status (e.g., Draft, In Review, Approved, Released) of every item and baseline.
- **Configuration Audits:** Tooling must support automated Functional Configuration Audits (FCA) and Physical Configuration Audits (PCA) to verify that the delivered baseline matches the authorized requirements and physical content expectations.

## 4. Access, Retention, and Backup
- **Access Controls:** Strict access rights must be enforced. Only authorized roles (e.g., Integrator) may commit to protected integration branches or create baselines.
- **Backup & Recovery:** The entire CM repository must undergo regular, documented backup and restore tests to ensure data availability.
- **Retention:** All records and evidence must be retained in accordance with the project's compliance and liability retention policies.
