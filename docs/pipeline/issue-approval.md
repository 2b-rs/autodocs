# Issue Architecture Approval Bootstrap

The bootstrap procedure reads all policy from the exact review-package commit, verifies the approval-ref commit and approval record digests with `git verify-commit`, and requires repository-owner fingerprint confirmation via a recorded independent channel before trusting the first policy. Private key material is never stored or requested. Task `0037-49` proves the external signing, reviewer, hosting-administration, and credential readiness required to use this procedure.
