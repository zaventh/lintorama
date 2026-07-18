# lintorama

> One Docker image, many linters, a single command.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Base image](https://img.shields.io/badge/base-python%3A3--alpine3.24-blue.svg)
![Linters](https://img.shields.io/badge/linters-5-brightgreen.svg)

`lintorama` bundles several linters behind one entrypoint, `lint-extras`, for use
in CI pipelines. Point it at a Git repository and it runs the appropriate linter
over each tracked file type, returning a non-zero exit code if any check fails —
no per-project linter installs, no juggling versions.

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

The repository must be a local Git checkout, and its `.git` directory must be
available inside the container (the linters enumerate files via Git):

```sh
docker run --rm \
  -v "$PWD":/code \
  -v "$PWD"/.git:/code/.git \
  zaventh/lintorama:5
```

The image works out of `/code` (its `WORKDIR`), which is already registered as a
Git `safe.directory`.

### In a GitLab CI pipeline

```yaml
lint:
  image: zaventh/lintorama:5
  script:
    - lint-extras
```

## What it checks

The `lint-extras` entrypoint operates on the **Git-tracked** files in the working
directory (it uses `git ls-files`), so the target must be a Git repository.
In order, it:

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

Each linter honors its standard configuration file when present in the repository
root, so consumers can tune the rules without changing this image:

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

## Building & releasing

The image is built and pushed by `.gitlab-ci.yml` on every push to the default
branch. To cut a new release, bump the `BUILD_VER` variable in that file
(semver, e.g. `5.3.0`); the pipeline publishes the full version, the major tag,
and `latest` to both registries, stamps the version, build date, and commit SHA
into the image's OCI labels, and syncs this README to the Docker Hub repository
description.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2016-2026 Jeff Mixon.
