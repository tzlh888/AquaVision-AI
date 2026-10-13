# Legacy Link Resolution

Date: 2026-10-13

## Scope

This audit examined eight unresolved repository-relative links in `data/metadata/phase5/README_before_phase5.md`. The file is a frozen snapshot of an earlier root README. Its links were valid as root-relative locations in that historical context but no longer resolve when interpreted relative to the snapshot's nested archive directory.

## Classification and decision

All eight links are classified **ARCHIVED**. Each intended target still exists at the repository-root path recorded in `LINK_EXCEPTION_REGISTRY.csv`. The snapshot is retained byte-for-byte because rewriting it would change preserved historical evidence merely to accommodate its later archive location.

The snapshot SHA-256 remains:

`4d56e2af2d551a09aa55f7f748ca7259b324ea3b2c568ec094fabb2d7233ad73`

No active README link is covered by this exception. No global Markdown-link check is disabled; link validation must apply the eight exact source/target exceptions only when it is intentionally scanning archived snapshots.

## Result

There are zero active-link repairs and eight documented archived exceptions. No frozen research artifact was modified.
