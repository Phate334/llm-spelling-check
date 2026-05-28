# Contributing

This document defines the branch, merge request, tag, and release guidelines for this project.

## Branch Model

`main` is the primary development branch. It must always be releasable, and all project changes must enter it through a merge request. Direct commits to `main` are allowed only for urgent repository administration that does not affect project behavior and cannot reasonably go through a merge request.

For daily development, create short-lived branches from the latest `main`. Use GitLab issue-prefixed branch names whenever possible so the branch can be associated with the issue:

```text
<issue-number>-<short-description>
```

Examples:

```text
123-add-user-settings
124-fix-login-validation
125-update-release-guide
```

Daily development branches are short-lived working branches. They may remain briefly after merge for traceability, but do not keep them as long-lived history markers.

Only use these special branch prefixes:

| Prefix | Use |
| --- | --- |
| `feature/<short-description>` | Work that spans multiple issues or may be released in a later version |
| `release/vX.Y.X` | Long-lived maintenance branch for an older minor version |

Keep branch names lowercase and use hyphens between words.

```bash
git checkout main
git pull --ff-only
git checkout -b 123-add-user-settings
git checkout -b feature/new-billing-flow
git checkout -b release/v1.1.X
```

Feature branches are temporary integration branches. Each feature branch must have an owner and a planned release target. They may remain briefly after merge while the related work is still being validated, but do not keep them as permanent development branches.

Release branches are used only when an older version line needs ongoing maintenance. Name them after the maintained minor version, such as `release/v1.1.X`. Keep release branches long term and apply maintenance fixes through merge requests. Do not merge `release/*` branches back into `main`; when the same fix is also needed on current development, apply it to `main` through a separate merge request.

## Merge Requests

Before merging a merge request:

- Keep the scope focused on one logical change.
- Rebase or merge the latest target branch when needed to resolve conflicts or refresh checks.
- Update documentation when behavior, configuration, public APIs, or release instructions change.
- Ensure required GitLab pipelines pass, especially for changes to source code, tests, deployment, dependencies, or release behavior.
- Link related GitLab issues in the description.
- Use `Closes #123` only when the merge request fully resolves the issue.

Use the repository's configured GitLab merge strategy. The recommended default is to squash daily development and feature branches with a clear squash commit message. Do not rewrite or force-push protected branch history.

Failed CI jobs must be fixed or explicitly accepted by a maintainer before merge. Do not skip CI for changes that affect project behavior, delivery, or release safety.

## GitLab Protection

The `main` branch should be protected in GitLab.

Recommended settings:

- Protect the `main` branch.
- Protect long-lived release branches matching `release/*`.
- Allow only Maintainers to push to protected branches.
- Require merge requests and successful pipelines before merge.
- Disable force push on protected branches.
- Protect release tags matching `v*`.
- Allow only Maintainers to create protected tags.
- Restrict tag deletion or updates when supported by the GitLab instance.

## Versioning and Tags

The Python package version is stored in `pyproject.toml` as `project.version`. Keep the package version and Git release tag aligned. Release tags use a `v` prefix and must follow Python PEP 440-compatible version identifiers:

```text
vMAJOR.MINOR.PATCH
```

Examples:

```text
v1.0.0
v1.1.0
v1.1.1
v1.2.0rc1
```

Use PEP 440 spelling for pre-releases. For release candidates, use `rcN` without a hyphen, such as `1.2.0rc1` for the Python package version and `v1.2.0rc1` for the Git tag.

Use `uv version --bump` to update `project.version` when using `uv >= 0.7.0`:

```bash
uv version --bump patch
# 1.2.0 => 1.2.1
uv version --bump minor
# 1.2.1 => 1.3.0
uv version --bump major
# 1.3.0 => 2.0.0
uv version --bump patch --bump rc
# 2.0.0 => 2.0.1rc1
uv version --bump stable
# 2.0.1rc1 => 2.0.1
```

Choose the next version with these rules:

| Bump | Use when |
| --- | --- |
| `MAJOR` | Making incompatible API, behavior, configuration, command, file, deployment, runtime, or platform changes |
| `MINOR` | Adding backward-compatible features, options, commands, or integrations |
| `PATCH` | Fixing bugs, documentation, release metadata, tests, tooling, or internal implementation without changing public behavior |

Tag rules:

- Create release tags from `main` for the current version line.
- Create maintenance patch tags from the relevant `release/vX.Y.X` branch when maintaining an older version line.
- Use annotated tags.
- Never reuse a published tag for a different commit.
- Do not delete or move a published tag unless the release is invalid and maintainers agree on the recovery plan.

Create a tag after the version change has been merged into the branch being released:

```bash
git checkout <release-branch>
git pull --ff-only
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Verify a tag:

```bash
git show vX.Y.Z
```

## Release Workflow

1. Update `project.version` in the release change branch, preferably with `uv version --bump`.
2. Merge the release change into `main` for the current version line, or into the relevant `release/vX.Y.X` branch for an older maintained version line.
3. Create and push an annotated tag from the branch being released.
4. Publish release notes with user-facing changes, fixes, and migration notes.

Example release candidate flow:

```bash
git checkout feature/export
uv version --bump patch --bump rc
git push origin feature/export
```

Open a merge request from `feature/export` to `main`. After review and successful pipelines, merge it using the repository's configured GitLab merge strategy, preferably squash merge. Do not merge locally or push directly to `main`.

After the merge request has been merged, create the release tag from the updated target branch:

```bash
git checkout main
git pull --ff-only

git tag -a v1.0.1rc1 -m "Release v1.0.1rc1"
git push origin v1.0.1rc1
```

## Maintenance Workflow

Use a maintenance release when an older released version needs a patch.

1. Create the maintenance fix branch from the relevant `release/vX.Y.X` branch.
2. Apply the smallest fix that resolves the issue.
3. Run the relevant checks.
4. Merge the fix into the release branch through a merge request.
5. Create and push the new patch tag from the release branch.
6. If the fix also applies to current development, apply it to `main` through a separate merge request. Do not merge the `release/*` branch back to `main`.

Do not move the broken tag. Release a new patch version instead.
