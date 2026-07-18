#!/usr/bin/env bash
# lint-extras.sh
# Version 3.1.2
declare -i RESULT=0
shopt -s dotglob

# lint all yaml committed
# shellcheck disable=2207
files=( $(git ls-files '*.yml' '*.yaml') )
[ ${#files[@]} -eq 0 ] || yamllint -s -- "${files[@]}"
RESULT+=$?

# ensure yarn.lock
if test -f package.json; then
  if ! test -f yarn.lock; then
    echo 'No yarn.lock file present'
    RESULT+=1
  fi
fi

# lint shell files
# shellcheck disable=2207
files=( $(git ls-files '*.sh' '*.bash') )
[ ${#files[@]} -eq 0 ] || shellcheck "${files[@]}"
RESULT+=$?

# lint lua files
# shellcheck disable=2207
files=( $(git ls-files '*.lua') )
[ ${#files[@]} -eq 0 ] || luacheck -q "${files[@]}"
RESULT+=$?

# lint Dockerfile
if test -f Dockerfile; then
  hadolint Dockerfile
  RESULT+=$?
fi

# lint markdown
if ! test -f README.md; then
  echo 'You must have at least a README.md (case sensitive)'
  RESULT+=1
fi

shopt -s extglob
# shellcheck disable=2207
files=( $(git ls-files '*.md' '*.markdown') )
[ ${#files[@]} -eq 0 ] || mdl "${files[@]}"
RESULT+=$?

if [ -d ".gitlab" ]; then
  mdl -- .gitlab
  RESULT+=$?
fi

exit $RESULT
