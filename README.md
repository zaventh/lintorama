# lintorama

> One Docker image, many linters, a single command.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Source](https://img.shields.io/badge/source-GitHub-181717.svg?logo=github)](https://github.com/zaventh/lintorama)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-zaventh%2Flintorama-2496ED.svg?logo=docker&logoColor=white)](https://hub.docker.com/r/zaventh/lintorama)
![Base image](https://img.shields.io/badge/base-python%3A3--alpine3.24-blue.svg)
![Linters](https://img.shields.io/badge/linters-5-brightgreen.svg)

**lintorama** is a single Docker image that bundles five widely-used code
linters — [yamllint](https://github.com/adrienverge/yamllint),
[ShellCheck](https://www.shellcheck.net/),
[hadolint](https://github.com/hadolint/hadolint),
[markdownlint (mdl)](https://github.com/markdownlint/markdownlint), and
[luacheck](https://github.com/lunarmodules/luacheck) — behind one entrypoint,
`lint-extras`. Point it at a Git repository and it runs the right linter over
every tracked YAML, shell, Lua, `Dockerfile`, and Markdown file, then exits
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

- **Five linters, one image.** YAML, shell, `Dockerfile`, Markdown, and Lua are
  all covered by a single pull.
- **Zero setup to start.** Sensible defaults work out of the box; every linter
  still honors its own config file when you want to tune it.
- **CI-native.** A single `lint-extras` command lints an entire repository and
  returns a meaningful exit code for your pipeline.
- **Reproducible.** Tool versions are pinned in the image, so every run uses the
  exact same linters everywhere.
- **Small footprint.** Built on `python:3-alpine3.24`.

## Bundled linters

| Tool | Version | Checks |
| --- | --- | --- |
| [yamllint](https://github.com/adrienverge/yamllint) | 1.38.0 | YAML (`*.yml`, `*.yaml`) |
| [ShellCheck](https://www.shellcheck.net/) | 0.11.0 | Shell scripts (`*.sh`, `*.bash`) |
| [hadolint](https://github.com/hadolint/hadolint) | 2.14.0 | `Dockerfile` |
| [markdownlint (mdl)](https://github.com/markdownlint/markdownlint) | 0.17.0 | Markdown (`*.md`, `*.markdown`) |
| [luacheck](https://github.com/lunarmodules/luacheck) | 1.2.0 | Lua (`*.lua`) |

Built on `python:3-alpine3.24`.

## Quick start

The target must be a local Git checkout, and its `.git` directory has to be
available inside the container — the linters enumerate files with `git ls-files`:

```sh
docker run --rm \
  -v "$PWD":/code \
  -v "$PWD"/.git:/code/.git \
  zaventh/lintorama:5
```

The image works out of `/code` (its `WORKDIR`), which is already registered as a
Git `safe.directory`. That is the only requirement — run the command from the
root of any Git repository and it lints every supported file type.

## Continuous integration

`lint-extras` is the image's entrypoint, so most CI systems need only a few
lines. The examples below all run the full linter suite over the checked-out
repository and fail the job on any lint error.

### GitLab CI

```yaml
lint:
  image: zaventh/lintorama:5
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
          docker run --rm \
            -v "$PWD":/code \
            -v "$PWD"/.git:/code/.git \
            zaventh/lintorama:5
```

### Any other CI (generic Docker)

```sh
docker run --rm \
  -v "$PWD":/code \
  -v "$PWD"/.git:/code/.git \
  zaventh/lintorama:5
```

## What it checks

The `lint-extras` entrypoint operates on the **Git-tracked** files in the
working directory (it uses `git ls-files`), so the target must be a Git
repository. In order, it:

1. Runs `yamllint -s` (strict) over all tracked `*.yml` / `*.yaml` files.
1. If a `package.json` exists, requires a `yarn.lock` or `package-lock.json` to accompany it.
1. Runs `shellcheck` over all tracked `*.sh` / `*.bash` files.
1. Runs `luacheck` over all tracked `*.lua` files.
1. Runs `hadolint` against `Dockerfile`, if present.
1. Requires a `README.md` (case-sensitive) to exist.
1. Runs `mdl` over all tracked `*.md` / `*.markdown` files.

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

The config files in this repository are the ones `lintorama` applies to itself.

## Image tags

Published to Docker Hub as
[`zaventh/lintorama`](https://hub.docker.com/r/zaventh/lintorama):

| Tag | Meaning |
| --- | --- |
| `5.3.0` | Exact, immutable version |
| `5` | Rolling major tag (recommended for most pipelines) |
| `latest` | The most recent build |

## FAQ

**What is lintorama?**
lintorama is a Docker image that bundles yamllint, ShellCheck, hadolint,
markdownlint (mdl), and luacheck behind a single command, `lint-extras`, for
linting a Git repository in CI pipelines.

**Which linters does lintorama include?**
Five: yamllint (YAML), ShellCheck (shell scripts), hadolint (`Dockerfile`),
markdownlint / mdl (Markdown), and luacheck (Lua). See
[Bundled linters](#bundled-linters) for exact versions.

**How do I run lintorama locally?**
Run `docker run --rm -v "$PWD":/code -v "$PWD"/.git:/code/.git zaventh/lintorama:5`
from the root of any Git repository. See [Quick start](#quick-start).

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
repository with its `.git` directory available inside the container.

**How does lintorama report failures?**
The exit code is the sum of the individual linters' results, so a non-zero exit
means at least one check failed — exactly what a CI pipeline needs.

**Where is the image published?**
On Docker Hub as
[`zaventh/lintorama`](https://hub.docker.com/r/zaventh/lintorama). The source
lives on [GitHub](https://github.com/zaventh/lintorama).

## Building and releasing

The image is built and pushed by `.gitlab-ci.yml` on every push to the default
branch. To cut a new release, bump the `BUILD_VER` variable in that file
(semver, e.g. `5.3.0`); the pipeline publishes the full version, the major tag,
and `latest`, stamps the version, build date, and commit SHA into the image's
OCI labels, and syncs this README to the Docker Hub repository description.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2016-2026 Jeff Mixon.
