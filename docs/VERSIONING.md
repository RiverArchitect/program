Semantic Versioning
===================

River Architect uses a [semantic versioning](https://semver.org/) scheme with the following format:

`[major].[minor].[patch]-[stable/beta]`

where

- `[major]` is incremented in the case of major changes in software and backward-incompatible releases.

- `[minor]` incremented in the case of backward compatible APIs (here: adding a new tab to the River Architect GUI).

- `[patch]` is incremented after a bug fix.

- `[stable/beta]` describe if the version is fully tested and runs stable or if there is uncertainty in the code functionality (not fully tested).

***

## Implementation in `Git`

Add a tag: `git tag -a "v1.1.0-beta" -m "version v1.1.0-beta"` (example for version v1.1.0)

Every new commit after adding this tag will auto-increment the tag by appending a commit number and hash. The version change after a commit can be viewed using `git describe` (returns e.g., `v1.1.0-beta-1-g5a6e47f`, where `1` indicates the commit number and `g` the commit's hash). Alternatively, `git show v1.1.0-beta` shows all commit details. 