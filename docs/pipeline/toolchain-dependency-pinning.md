# Toolchain & Dependency Pinning (Feature 0015-04)

## Purpose
This document establishes the architecture for strict toolchain and dependency pinning. It ensures that any baseline or campaign execution can be deterministically reproduced from a clean checkout, independent of external state or shifting network dependencies.

## 1. Pinning Requirements
Every project repository must explicitly declare its full dependency tree with exact content hashes.
- **Python:** Use `requirements.txt` generated with hashes (`pip-compile --generate-hashes`), or equivalent strictly pinned `poetry.lock` / `Pipfile.lock`.
- **Node.js:** Use `package-lock.json` or `yarn.lock` with integrity hashes for all transitives.
- **System Tools:** Critical system tools (e.g., compilers, generators) must be specified by exact version. Where feasible, container images (e.g., Dockerfiles) must reference base images by their immutable `@sha256:...` digest, not mutable tags like `:latest` or `:v1.2`.

## 2. External Input Identities
Any external file or asset downloaded during build or test must be verified against a recorded cryptographic hash (SHA-256). The build process must immediately fail if the hash of an external input does not match the recorded identity.

## 3. Deterministic Clean-Checkout Restoration
The build and CI environment must guarantee deterministic restoration:
- **No Moving References:** Builds must not fetch dependencies from floating references. If an upstream package is deleted or mutated, the local build must fail or rely on a controlled internal proxy/cache, never silently pull a different version.
- **Undeclared State Prohibition:** The build must execute successfully in a completely isolated environment (e.g., a clean container with disabled network access for fetch steps, once the cache is populated) to prove that no undeclared environment variables or local user states are influencing the outcome.

## 4. Verification & Auditing
Before a baseline is approved (Feature 0015-03), an automated audit must verify:
- All lockfiles are present and up-to-date with their respective manifests.
- The build succeeds in an ephemeral, clean-checkout environment.
- Any deviations or missing hashes trigger an immediate verification failure.
