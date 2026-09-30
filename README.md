<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.png">
    <img src="assets/logo.png" alt="lintorama — one Docker image, many linters, a single command" width="480">
  </picture>
</p>


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Source](https://img.shields.io/badge/source-GitHub-181717.svg?logo=github)](https://github.com/zaventh/lintorama)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-zaventh%2Flintorama-2496ED.svg?logo=docker&logoColor=white)](https://hub.docker.com/r/zaventh/lintorama)
![Base image](https://img.shields.io/badge/base-python%3A3--alpine3.24-blue.svg)
![Linters](https://img.shields.io/badge/linters-8-brightgreen.svg)

# lintorama

**lintorama** is a single Docker image that bundles eight widely-used linters
and validators — [yamllint](https://github.com/adrienverge/yamllint),
[ShellCheck](https://www.shellcheck.net/),
[hadolint](https://github.com/hadolint/hadolint),
[markdownlint (mdl)](https://github.com/markdownlint/markdownlint),
[luacheck](https://github.com/lunarmodules/luacheck),
[actionlint](https://github.com/rhysd/actionlint),
[check-jsonschema](https://github.com/python-jsonschema/check-jsonschema), and
[editorconfig-checker](https://github.com/editorconfig-checker/editorconfig-checker)
— behind one entrypoint, `lint-extras`. Point it at a Git repository and it runs
the right check over every tracked YAML, shell, Lua, `Dockerfile`, Markdown, and
GitHub Actions workflow file, schema-validates common config files
(`.gitlab-ci.yml`, Dependabot, Renovate, Read the Docs), and — when an
`.editorconfig` is present — verifies every tracked file against it, then exits
non-zero if any check fails. It is built for CI pipelines: no per-project linter
installs, no juggling tool versions, no bespoke setup — just `docker run`.

In short: **one container image for polyglot static analysis and code-quality
checks in continuous integration.**

## Contents

- [Highlights](#highlights)
- [Bundled linters](#bundled-linters)
- [Quick start](#quick-start)
- [Continuous integration](#continuous-integration)
- [What it checks](#what-it-checks)
- [Configuration](#configuration)
- [Image tags](#image-tags)
- [FAQ](#faq)
- [Building and releasing](#building-and-releasing)
- [License](#license)

## Highlights

- **Eight checks, one image.** YAML, shell, `Dockerfile`, Markdown, Lua, GitHub
  Actions workflows, schema-backed config files, and `.editorconfig` conformance
  are all covered by a single pull.
- **Zero setup to start.** Sensible defaults work out of the box; every linter
  still honors its own config file when you want to tune it.
- **CI-native.** A single `lint-extras` command lints an entire repository and
  returns a meaningful exit code for your pipeline.
- **Reproducible.** Tool versions are pinned in the image, so every run uses the
  exact same linters everywhere.
- **Small footprint.** Built on `python:3-alpine3.24`.
- **Native on amd64 and arm64.** Every tag is a multi-arch image, so it runs
  without emulation on x86-64 CI runners and on Apple Silicon Macs alike.

## Bundled linters

| Tool | Version | Checks |
| --- | --- | --- |
| [yamllint](https://github.com/adrienverge/yamllint) | 1.38.0 | YAML (`*.yml`, `*.yaml`) |
| [ShellCheck](https://www.shellcheck.net/) | 0.11.0 | Shell scripts (`*.sh`, `*.bash`) |
| [hadolint](https://github.com/hadolint/hadolint) | 2.15.1 | `Dockerfile` |
| [markdownlint (mdl)](https://github.com/markdownlint/markdownlint) | 0.18.1 | Markdown (`*.md`, `*.markdown`) |
| [luacheck](https://github.com/lunarmodules/luacheck) | 1.2.0 | Lua (`*.lua`) |
| [actionlint](https://github.com/rhysd/actionlint) | 1.7.12 | GitHub Actions workflows (`.github/workflows/*.yml`) |
| [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) | 0.38.0 | Schema validation: `.gitlab-ci.yml`, Dependabot, Renovate, Read the Docs |
| [editorconfig-checker](https://github.com/editorconfig-checker/editorconfig-checker) | 4.0.1 | `.editorconfig` conformance (all tracked files) |

Built on `python:3-alpine3.24`.

## Quick start

The target must be a local Git checkout, and its Git directory has to be
available inside the container — the linters enumerate files with `git ls-files`:

```sh
gitdir=$(git rev-parse --path-format=absolute --git-common-dir)
docker run --rm \
  -v "$PWD":/code \
  -v "$gitdir":"$gitdir" \
  zaventh/lintorama:7
```

The image works out of `/code` (its `WORKDIR`), which is already registered as a
Git `safe.directory`. That is the only requirement — run the command from the
root of any Git repository, or any of its worktrees, and it lints every
supported file type.

### Git worktrees

In a regular checkout, `.git` is a directory and the first mount already brings
it into `/code`. In a linked worktree (`git worktree add`), `.git` is a file
pointing into the main repository's Git directory, for example
`gitdir: /home/me/project/.git/worktrees/feature`. The second mount puts that
directory at the same path inside the container, so the pointer resolves. In a
regular checkout it's redundant but harmless, so the same command works in both
cases.

Worktrees created with `git worktree add --relative-paths` (or
`worktree.useRelativePaths`) store a relative pointer instead, which only
resolves if the worktree keeps its host path in the container. Mount it there
and mark that path as a Git `safe.directory`:

```sh
gitdir=$(git rev-parse --path-format=absolute --git-common-dir)
docker run --rm \
  -v "$PWD":"$PWD" -w "$PWD" \
  -v "$gitdir":"$gitdir" \
  -e GIT_CONFIG_COUNT=1 \
  -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0="$PWD" \
  zaventh/lintorama:7
```

## Continuous integration

`lint-extras` is the image's entrypoint, so most CI systems need only a few
lines. The examples below all run the full linter suite over the checked-out
repository and fail the job on any lint error.

### GitLab CI

```yaml
lint:
  image: zaventh/lintorama:7
  script:
    - lint-extras
```

### GitHub Actions

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run lintorama
        run: |
          gitdir=$(git rev-parse --path-format=absolute --git-common-dir)
          docker run --rm \
            -v "$PWD":/code \
            -v "$gitdir":"$gitdir" \
            zaventh/lintorama:7
```

### Any other CI (generic Docker)

```sh
gitdir=$(git rev-parse --path-format=absolute --git-common-dir)
docker run --rm \
  -v "$PWD":/code \
  -v "$gitdir":"$gitdir" \
  zaventh/lintorama:7
```

## What it checks

The `lint-extras` entrypoint operates on the **Git-tracked** files in the
working directory (it uses `git ls-files`), so the target must be a Git
repository. In order, it:

1. Runs `yamllint -s` (strict) over all tracked `*.yml` / `*.yaml` files.
1. Schema-validates well-known config files against their published schemas with `check-jsonschema`, when present: `.gitlab-ci.yml`, `.github/dependabot.yml`, Renovate config (`renovate.json`, `.renovaterc`, …), and `.readthedocs.yaml`.
1. Runs `actionlint` over all tracked `.github/workflows/*.yml` / `*.yaml` files (delegating embedded `run:` scripts to the bundled ShellCheck).
1. If a `package.json` exists, requires a `yarn.lock` or `package-lock.json` to accompany it.
1. Runs `shellcheck` over all tracked `*.sh` / `*.bash` files.
1. Runs `luacheck` over all tracked `*.lua` files.
1. Runs `hadolint` against `Dockerfile`, if present.
1. Requires a `README.md` (case-sensitive) to exist.
1. Runs `mdl` over all tracked `*.md` / `*.markdown` files.
1. If an `.editorconfig` exists, runs `editorconfig-checker` to verify every tracked file conforms to it.

The exit code is the sum of the individual linter results — any failure fails
the run.

## Configuration

Each linter honors its standard configuration file when present in the
repository root, so consumers can tune the rules without changing this image:

| File | Linter |
| --- | --- |
| `.yamllint` | yamllint |
| `.hadolint.yaml` | hadolint |
| `.mdlrc` | markdownlint |
| `.github/actionlint.yaml` | actionlint |
| `.editorconfig` | editorconfig-checker (also the file it enforces) |

The `.yamllint`, `.hadolint.yaml`, `.mdlrc`, and `.editorconfig` files in this
repository are the ones `lintorama` applies to itself. `check-jsonschema` needs
no configuration — it picks each file's schema by name — and
`editorconfig-checker` only runs when the repository provides an `.editorconfig`.

## Image tags

Published to Docker Hub as
[`zaventh/lintorama`](https://hub.docker.com/r/zaventh/lintorama):

| Tag | Meaning |
| --- | --- |
| `7.1.1` | Exact, immutable version |
| `7` | Rolling major tag (recommended for most pipelines) |
| `latest` | The most recent build |

Each tag is a multi-arch image for `linux/amd64` and `linux/arm64`; Docker picks
the right one for the host automatically.

## FAQ

**What is lintorama?**
lintorama is a Docker image that bundles yamllint, ShellCheck, hadolint,
markdownlint (mdl), luacheck, actionlint, check-jsonschema, and
editorconfig-checker behind a single command, `lint-extras`, for linting a Git
repository in CI pipelines.

**Which linters does lintorama include?**
Eight: yamllint (YAML), ShellCheck (shell scripts), hadolint (`Dockerfile`),
markdownlint / mdl (Markdown), luacheck (Lua), actionlint (GitHub Actions
workflows), check-jsonschema (schema validation for CI and tooling config), and
editorconfig-checker (`.editorconfig` conformance). See
[Bundled linters](#bundled-linters) for exact versions.

**How do I run lintorama locally?**
Run the [Quick start](#quick-start) command from the root of any Git repository
or worktree: it mounts the checkout at `/code` and the repository's Git
directory at its host path.

**How do I use lintorama in CI?**
In GitLab CI, use it as the job `image` and call `lint-extras`. In GitHub
Actions or any other system, run the image with `docker run`. See
[Continuous integration](#continuous-integration).

**Does lintorama require configuration?**
No. It works with sensible defaults, but each linter honors its standard config
file (`.yamllint`, `.hadolint.yaml`, `.mdlrc`) when present. See
[Configuration](#configuration).

**Why does lintorama need the `.git` directory?**
`lint-extras` discovers files with `git ls-files`, so the target must be a Git
repository with its Git directory available inside the container. For a
worktree, that means the main repository's Git directory too. See
[Git worktrees](#git-worktrees).

**How does lintorama report failures?**
The exit code is the sum of the individual linters' results, so a non-zero exit
means at least one check failed — exactly what a CI pipeline needs.

**Does lintorama run on Apple Silicon or other arm64 hosts?**
Yes. Every tag includes a native `linux/arm64` image next to `linux/amd64`, so
Docker on an Apple Silicon Mac runs it without Rosetta or QEMU emulation.

**Where is the image published?**
On Docker Hub as
[`zaventh/lintorama`](https://hub.docker.com/r/zaventh/lintorama). The source
lives on [GitHub](https://github.com/zaventh/lintorama).

## Building and releasing

The image is built and pushed by `.gitlab-ci.yml` on every push to the default
branch. Each architecture is built natively on its own runner — `linux/amd64` on
a Linux runner, `linux/arm64` on an Apple Silicon Mac runner (tagged `macos`) —
and linted with that same image before anything is published. To cut a new
release, bump the `BUILD_VER` variable in that file (semver, e.g. `7.1.0`); the
pipeline then combines both builds into one multi-arch image, publishes it as the
full version, the major tag, and `latest`, stamps the version, build date, and
commit SHA into the image's OCI labels, and syncs this README to the Docker Hub
repository description.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2016-2026 Jeff Mixon.
