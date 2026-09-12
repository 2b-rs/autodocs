# MAN.5 ECU Risk Management Strategy

## 1. Purpose and Scope
This document defines the risk management strategy for the ECU project in accordance with ASPICE MAN.5 requirements. It establishes the criteria, categorization, and operational procedures for identifying, analyzing, mitigating, and monitoring risks throughout the ECU lifecycle.

## 2. Risk Categories
To ensure comprehensive coverage, risks are identified across the following dimensions:
- **Technical**: Architecture limits, hardware constraints, performance bottlenecks.
- **Schedule**: Milestone delays, critical path blockers.
- **Resource**: Personnel availability, skill gaps, budget overruns.
- **Supplier**: Delays or quality issues from external vendors.
- **Integration**: Challenges in hardware/software integration.
- **Verification/Validation**: Inadequate test coverage, critical defects.
- **Release**: Deployment failures, SPL.2 specification violations.
- **Tool**: Toolchain qualification issues (e.g., compilers, static analysis).
- **Safety-Interface**: ISO 26262 ASIL non-compliance.
- **Cybersecurity-Interface**: ISO/SAE 21434 vulnerabilities.
- **External-Dependency**: Upstream project delays, OEM timeline changes.

## 3. Risk Evaluation Criteria (Exposure)
Risk Exposure is calculated as `Probability × Impact`.

### Probability Rating (1-5)
1. Rare (< 10%)
2. Unlikely (10-30%)
3. Possible (31-60%)
4. Likely (61-90%)
5. Almost Certain (> 90%)

### Impact Rating (1-5)
1. Negligible (Minimal effort to recover)
2. Minor (Minor schedule slip, no critical path impact)
3. Moderate (Schedule delay < 2 weeks, minor performance degradation)
4. Major (Significant schedule delay, requires escalation, ASIL risk)
5. Severe (Project failure, safety/cybersecurity critical breach)

### Exposure Thresholds
- **Low (1-6)**: Acceptable. Monitor via standard reviews.
- **Medium (7-14)**: Requires mitigation plan. Monitor actively.
- **High (15-25)**: Requires immediate escalation, active treatment, and executive oversight.

## 4. Risk Treatment and Residual Acceptance
For each identified risk (especially Medium and High), a treatment strategy must be defined:
- **Avoid**: Change plans to bypass the risk.
- **Mitigate**: Take actions to reduce probability or impact.
- **Transfer**: Shift the risk to a third party (e.g., supplier).
- **Accept**: Acknowledge the risk without active mitigation (requires Management Approval for Medium/High risks).

**Residual Risk** is the exposure calculated *after* treatment actions are applied. Residual High risks are not acceptable for A-Sample and beyond without explicit project sponsor sign-off.

## 5. Monitoring and Effectiveness
- The Risk Register is reviewed bi-weekly in the MAN.3 project synchronization meeting.
- High risks are reviewed weekly.
- Mitigation effectiveness is assessed at each review: if exposure does not decrease as planned, escalation is required.

## 6. Escalation and Closure
- **Escalation**: Any risk crossing into the "High" threshold, or a mitigation plan failing its effectiveness check, is escalated to the Project Lead and explicitly flagged in Management Reviews.
- **Closure**: A risk is marked Closed when the probability reaches 0 (e.g., the milestone passed successfully) or the residual impact is confirmed negligible. Closure evidence must be recorded.

## 7. Maintained Register Schema
The active Risk Register is maintained as structured data tracking the following fields for each entry:
- `ID`: Unique identifier
- `Category`: One of the categories listed in Section 2.
- `Description`: Clear statement of the condition and consequence.
- `Initial_Exposure`: Initial Probability × Impact.
- `Treatment_Plan`: Actionable mitigation steps.
- `Owner`: Responsible individual.
- `Residual_Exposure`: Expected probability/impact post-treatment.
- `Status`: Open, Mitigated, Escalated, Closed.
- `Effectiveness_Log`: Periodic updates on mitigation success.
- `Closure_Evidence`: Justification and artifact links for closure.
