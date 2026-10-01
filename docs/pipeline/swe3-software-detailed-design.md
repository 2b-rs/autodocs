# SWE.3 ECU Software Detailed Design

## 1. Overview
This document baselines the SWE.3 ECU Software Detailed Design. It defines unit-level contracts, static and dynamic behavior, data/control flows, and algorithms for all in-scope software units derived from the SWE.2 Software Architecture.

## 2. Unit and Interface Contracts
Detailed design contracts are defined for the major components:
* **SW-CORE (Core OS):**
  * `Core_Task_Init(const TaskConfig_t* cfg)`: Initializes scheduler structures. Precondition: MCU initialized. Postcondition: Task added to ready queue.
  * `Core_IPC_Send(uint8_t qid, void* data, uint16_t len)`: Non-blocking send. Returns `E_OK` or `E_QUEUE_FULL`.
* **SW-DRV (Drivers):**
  * `Drv_ADC_Read(uint8_t channel, uint16_t* value)`: Synchronous read of ADC. Time bound: < 10us.
  * `Drv_CAN_Transmit(const CanMsg_t* msg)`: Pushes message to hardware buffer.
* **SW-APP (Application):**
  * `App_ControlLoop_10ms(void)`: Main control algorithm. Reads filtered sensor data, updates PI controller state, outputs actuator commands.
  * `App_ML_Inference(const float* features, float* output)`: Wraps the TensorFlow Lite Micro model execution.

## 3. Static & Dynamic Behavior
* **Control Flow:** The 10ms control loop strictly executes: `Read Inputs -> Filter -> PI Control -> ML Inference -> Write Outputs`.
* **Data Flow:** Sensor data is passed by value. ML inference uses a shared, lock-free static buffer to avoid heap allocation.
* **Concurrency Constraints:** Interrupt Service Routines (ISRs) for CAN and ADC must complete in < 50us and never call blocking functions. Data consistency between ISR and Tasks is ensured via interrupt-masking (short critical sections).

## 4. Algorithms & Coding Principles
* **Algorithms:** The PI controller uses a trapezoidal integration method with anti-windup (limit ±100). The ML model is pre-quantized (int8) to meet performance targets.
* **Coding Principles:** MISRA C:2012 compliance is mandatory. Dynamic memory allocation (e.g., `malloc`) is strictly prohibited. Maximum cyclomatic complexity is 15 per function.
* **Model/Generated-Code Boundaries:** The ML inference engine is generated code (TargetLink/TFLite) bounded within the `SW-APP/ML` namespace. No manual editing of generated files is permitted.

## 5. Traceability
* **To Architecture (SWE.2):** Each unit function is traced to a corresponding SWE.2 architectural component and interface.
* **To Requirements (SWE.1):** The detailed design traces to the allocated SWE.1 requirements.
* Complete traceability matrix is maintained in `SWE3-DESIGN-TRACE-20260912`.

## 6. Approvals
The detailed design is approved for SWE.4 Unit Construction (coding) and SWE.4 Unit Verification planning.
