# Changes and releases

This page provides more details into how we keep track of our changes and how releases work based on `CHANGELOG.md` and Github actions.

## Updating the changelog
Every change should be documented in the `## [Unreleased]` section of [`CHANGELOG.md`](changelog.md), at the root of the repository, as part of the PR that makes the change. Entries are grouped under `### Added`, `### Changed`, `### Fixed` or `### Removed`. Changes that break existing configs or change the results of a default run should be marked as **Breaking** and explain how to recover the previous behavior. The [Changelog](changelog.md) page of this documentation is generated from this file.

## Releasing a new version
Fetpype follows [semantic versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`):

- **Major**: changes that can break existing usage, for instance removing or renaming config keys, CLI flags or outputs, or changing the results of a default run.
- **Minor**: new backward-compatible features, for instance a new method or a new optional config.
- **Patch**: bug fixes and documentation changes.

Versions are managed with [bump-my-version](https://github.com/callowayproject/bump-my-version), which is included in the dev dependencies. To make a release, run it in a branch and open a PR to `main`:
```
bump-my-version show-bump    # preview the possible versions
bump-my-version bump minor   # or patch / major
git push
```
This creates a single commit that updates the version in `pyproject.toml` and `fetpype/_version.py`, the version and `date-released` in `citation.cff`, and turns the `## [Unreleased]` section of `CHANGELOG.md` into `## [<version>] - <date>`. It refuses to run if tracked files have uncommitted changes.

Once the PR is merged, the `Release` GitHub workflow (`.github/workflows/release.yml`) runs on `main` and does a release as follows:

1. It reads the version from `fetpype/_version.py`.
2. If a `v<version>` tag already exists, it does nothing: merges that do not bump the version never create a release.
3. Otherwise, it creates the `v<version>` tag on the merged commit and a GitHub release whose notes are the `<version>` section of `CHANGELOG.md`. The workflow fails if that section is missing.

Releases are therefore only made from `main`, and only when a new version is merged. The documentation, including the changelog, is redeployed on the same push.

## Manually checking a version before publishing to pypi

1. **Build and check.**                                                                                            From the fetpype repository base, run
 ```                                                                                             
  rm -rf dist/ build/ *.egg-info
  python -m build
  twine check dist/*
```
2. Upload on `testpypi` after having setup an API token

```
  twine upload --repository testpypi dist/*
```

Automatic if you've already set up `~/.pypirc`. If it has a [testpypi] section with your token, twine uses it. Otherwise, it prompts: the username is __token__ and the password is your TestPyPI token.

3. **Test the upload** Install it in a fresh environment
```
  python -m venv /tmp/fetpype_test
  source /tmp/fetpype_test/bin/activate
  pip install -i https://test.pypi.org/simple/ \
      --extra-index-url https://pypi.org/simple/ "fetpype==2.0.0rc1"
```

Then test the commands on your data (e.g. `fetpype_run --help`, a real pipeline run).

4. **On rele**