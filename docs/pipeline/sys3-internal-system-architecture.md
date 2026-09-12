# SYS.3 Internal System Architectural Design (Feature 0030-02)

## Purpose
This document establishes the baseline architecture for the internal `SYS.3` System Architectural Design process. It defines the structural and behavioral decomposition of the system requirements into explicit hardware, software, machine learning (ML), and external system elements.

## 1. System Components and Allocations
The system is decomposed into distinct, manageable components:
- **Component ID:** COMP-01
- **Component Name:** `Main Processing Unit (MPU)`
- **Allocation:** Hardware/Software
- **Description:** Central computation node running the core OS and application logic.
- **Traceability:** Allocates SYS-REQ-001 through SYS-REQ-010.

- **Component ID:** COMP-02
- **Component Name:** `Sensory Acquisition Module`
- **Allocation:** Hardware
- **Description:** High-frequency ADCs and digital signal processing arrays.
- **Traceability:** Allocates SYS-REQ-011 through SYS-REQ-015.

- **Component ID:** COMP-03
- **Component Name:** `Perception Engine`
- **Allocation:** Software/ML
- **Description:** Neural network inference engine for object detection and classification.
- **Traceability:** Allocates SYS-REQ-016 through SYS-REQ-020.

## 2. Interfaces and Dynamic Behavior
### 2.1 Static Interfaces
- **IF-01:** SPI communication between `Sensory Acquisition Module` and `Main Processing Unit`. Bandwidth: 10 Mbps.
- **IF-02:** Internal IPC (Shared Memory) between `Main Processing Unit` and `Perception Engine`. Latency constraint: < 5ms.

### 2.2 Dynamic Behavior
- **Initialization Mode:** Components initialize sequentially. `Main Processing Unit` bootloaders initialize first, followed by `Sensory Acquisition Module` power-up sequence, then `Perception Engine` weight loading.
- **Operational States:** Normal Mode, Degraded Mode (e.g., if IF-01 CRC errors exceed 5%, fall back to default safety state), and Safe Shutdown.

## 3. Resource Budgets and Consumption
- **CPU:** Maximum 70% utilization across all cores during Normal Mode.
- **Memory:** Maximum 80% RAM utilization (Dynamic allocation is prohibited during runtime; pre-allocated pools only).
- **Power:** Maximum peak draw < 15W.
- **Network/Bus:** Maximum 60% load on external CAN/Ethernet interfaces.

## 4. Evaluation of Alternatives and Rationale
- **Alternative A (Centralized Compute):** A single monolithic SoC handling both acquisition and perception. Rejected due to thermal constraints and inability to meet safety separation requirements.
- **Alternative B (Selected):** Segregated Acquisition (COMP-02) and Perception (COMP-03). Chosen because it physically isolates high-frequency noise from the ML inference hardware, reducing EMI risk and enabling modular independent testing.

## 5. Bidirectional Traceability
Every system requirement (`SYS-REQ-*`) mapped in the SYS.2 stakeholder baseline is allocated to at least one system element above. Trace matrices must be maintained to demonstrate completeness, ensuring no unallocated requirements and no orphan architecture elements.
