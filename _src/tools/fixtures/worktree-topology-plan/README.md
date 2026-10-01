# Worktree Topology Plan fixtures

The focused test module derives immutable cases from the Architect-owned example
template. Each mutation names and asserts the exact stable `WTP-*` finding code;
positive minimal/full plans are constructed without copying or modifying the
contract input. The committed-REF test creates an isolated temporary Git
repository and leaves a foreign dirty file byte-identical.
