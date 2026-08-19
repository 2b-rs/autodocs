# Additive provenance correction — 0039-03

**Purpose:** Correct the Base-Ref provenance defect identified as `0039-03-AR-002` without rewriting immutable implementation commit `054e658bbe53057ad504a772b3d1fc6c4de68fcd`.

## Bound Git objects

| Fact | Value |
| --- | --- |
| Substantive commit | `054e658bbe53057ad504a772b3d1fc6c4de68fcd` |
| Substantive tree | `31fc69f0dfbb5820c0dfbb4add46e4e03d9f95e9` |
| Declared Base-Ref | `4e34650aa8c3d4facac0aa4456f06cbd1c7d24a1` |
| Declared Base-Ref resolution | absent (`git cat-file -e <ref>^{commit}` exits `128`) |
| Actual sole parent | `4e34650aa896dbad8a77dfadd8e43d80a1ffe227` |
| Actual parent tree | `19c3f0d90983da8d16bbf196e3cc172e99766f3e` |
| Parent-to-substantive binary diff SHA-256 | `59fc424225422f7fef09d94fde8577ecf123ab274736851d8cbf9e489e6f6f4f` |

The Base-Ref line in the immutable commit is invalid. This correction binds the implementation to its Git-native parent, not to a replacement base. `git merge-base --is-ancestor 4e34650aa896dbad8a77dfadd8e43d80a1ffe227 054e658bbe53057ad504a772b3d1fc6c4de68fcd` exits `0`, proving the stated parent is reachable from the substantive commit.

## Prerequisite observation

`0039-02` has a corrected accepted record at `960594917f429c492d9bf0c94e5796b144029ffe` (tree `b432af57323f4813bc8b7407bb8d1a732bb3be9d`). This record is included only as a verifiable prerequisite observation; this bounded correction neither modifies `0039-02` nor makes an acceptance decision.

## Reproduction

```sh
git cat-file -e 4e34650aa8c3d4facac0aa4456f06cbd1c7d24a1^{commit}
git rev-parse 054e658bbe53057ad504a772b3d1fc6c4de68fcd^{}
git rev-parse 054e658bbe53057ad504a772b3d1fc6c4de68fcd^
git merge-base --is-ancestor 4e34650aa896dbad8a77dfadd8e43d80a1ffe227 054e658bbe53057ad504a772b3d1fc6c4de68fcd
git diff --binary 4e34650aa896dbad8a77dfadd8e43d80a1ffe227 054e658bbe53057ad504a772b3d1fc6c4de68fcd | shasum -a 256
```

Expected results: the first command exits `128`; the parent command yields `4e34650aa896dbad8a77dfadd8e43d80a1ffe227`; the ancestry command exits `0`; and the diff digest equals the value above.
