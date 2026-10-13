# Main Merge Diff Audit

Date: 2026-10-13

## Compared revisions

- Base: `main` / `origin/main` at `bd11eceaa7efa7ca785d5e466cf807312ed70df0`
- Reviewed research branch before this link-resolution commit: `9a3df416c85e443e092a3a45121326e4682d11ec`
- Relationship: the research branch is a direct three-commit descendant of the base; the remote base has no unknown update.

## Diff findings

- The previously reviewed branch diff contains 96 paths: 94 additions and 2 modifications, with no deletions.
- This Stage 4A change adds four governance records and deliberately does not modify the archived README snapshot.
- No model, raw raster, checkpoint, historical metric, frozen protocol, experiment configuration, result table, or provenance hash was modified by Stage 4A.
- No merge conflict was detected against `origin/main`.
- `RESEARCH_CONTRIBUTION_STATEMENT.md` is not tracked and is not part of the merge diff.
- No private absolute path, credential pattern, prohibited development-workspace path, or unauthorized third-party binary was found in the public diff.
- The README retains the `LIMITED` conclusion, 288 verified historical array pairs, six integrated CyAN V6 products, zero qualified independent High units, `0/0/0` Training/Validation/Confirmation units, no Phase 3B training, and the distinction between satellite proxy labels and field truth.
- Post-change verification passed the public suite with 122 passed, one expected incomplete-environment skip, and zero failures; all 60 research-upgrade checks passed. Of 263 checked repository-relative Markdown links, only the eight exact archived exceptions remain unresolved in place.

## Personal-claim review

The README section `What I Learned` uses first person and says the project changed when the dataset was verified. That wording may be appropriate, but repository evidence alone cannot prove who performed the verification, originated each decision, or independently understood each implementation step. The owner must confirm this paragraph before merge. The untracked contribution statement remains a separate unresolved human-review item.

## Assessment

The diff is technically suitable for a pull request after this local commit is pushed under separate authorization. Main merge remains conditional on owner review of the first-person README paragraph and normal GitHub branch review.
