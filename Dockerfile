# syntax=docker/dockerfile:1.3
FROM koalaman/shellcheck-alpine:v0.11.0 AS shellcheck
FROM hadolint/hadolint:v2.14.0-alpine AS dockerlint

FROM python:3-alpine3.24
ARG BUILD_VER
ARG BUILD_DATE
ARG BUILD_SHA

LABEL org.opencontainers.image.title="lintorama" \
      org.opencontainers.image.description="Several linters bundled behind one entrypoint (lint-extras) for CI pipelines." \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.url="https://hub.docker.com/r/zaventh/lintorama" \
      org.opencontainers.image.version=$BUILD_VER \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$BUILD_SHA

COPY --from=shellcheck /bin/shellcheck /usr/local/bin/shellcheck
COPY --from=dockerlint /bin/hadolint /usr/local/bin/hadolint

COPY files /

RUN \
    --mount=type=cache,target=/root/.cache/pip \
    apk add --no-cache bash build-base ruby ruby-dev git \
    lua5.3-dev luarocks5.3 \
    && gem install --no-document etc mdl:0.17.0 \
    && pip install --no-cache-dir yamllint==1.38.0 \
    && luarocks-5.3 install luacheck 1.2.0-1 \
    && git config --global --add safe.directory /code \
    # smoke tests
    && mdl -V \
    && hadolint -v \
    && shellcheck -V \
    && yamllint -v \
    && luacheck -v

ENV LUA_PATH='/usr/local/share/lua/5.3/?.lua;/usr/local/share/lua/5.3/?/init.lua;/usr/share/lua/5.3/?.lua;/usr/share/lua/5.3/?/init.lua;./?.lua;./?/init.lua'
ENV LUA_CPATH='/usr/local/lib/lua/5.3/?.so;/usr/lib/lua/5.3/?.so;./?.so'

WORKDIR /code

ENTRYPOINT ["/usr/local/bin/lint-extras"]
