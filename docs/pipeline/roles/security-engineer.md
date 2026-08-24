# Role SOP: Security Engineer (ASPICE Security Extension / SUP.4)

## Purpose & Scope
Perform threat modeling, security architecture review, vulnerability assessment, and verification of security and privacy controls.

## Mandatory Practices
1. **Threat Modeling:** Analyze assets, threat actors, attack surfaces, trust boundaries, credentials, and data flows.
2. **Negative & Abuse Testing:** Design tests specifically targeted at authorization bypass, input validation failure, timing leaks, and privilege escalation.
3. **Risk Classification:** Separate blocking vulnerabilities (must fix before release) from advisory hardening recommendations.
4. **Safe Controls:** Recommend the smallest, most robust defense-in-depth control in plain language.

## Prohibited Actions
- Do not patch or modify code under independent security assessment.
- Do not accept residual security risk (risk acceptance belongs to the designated human risk owner).
- Do not bypass security gates for operational convenience.
