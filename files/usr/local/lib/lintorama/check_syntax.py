"""Syntax-check JSON, JSONC, and TOML files for lint-extras.

Usage: check_syntax.py {json,jsonc,toml} FILE...

Prints one `path:line:column: message` line per problem and exits 1 if any file
fails. JSON is held to RFC 8259: no comments, trailing commas, NaN or Infinity,
duplicate keys, or byte order mark. JSONC also allows // and /* */ comments,
trailing commas, and a byte order mark, as TypeScript and VS Code do. TOML is
held to v1.0, since Python's tomllib and Gradle can't read v1.1 additions.
"""

import json
import re
import sys

import tomli

BOM = "\ufeff"

# A // or /* */ comment. The quantifiers can't backtrack, so a comment never ends
# early at a "]" or reaches past its own "*/".
COMMENT = r"//[^\n]*+|/\*[^*]*\*+(?:[^/*][^*]*\*+)*/"

# What has to be blanked out of JSONC to leave JSON. Strings are matched only so
# that comment markers and commas inside them are left alone.
JSONC_TOKEN = re.compile(
    rf"""
      (?P<string> "(?:[^"\\\n]|\\.)*" )
    | (?P<comment> {COMMENT} )
    | (?P<unclosed> /\* )
    | (?P<comma> ,(?=(?:\s|{COMMENT})*[\]}}]) )
    """,
    re.DOTALL | re.VERBOSE,
)

# Strings, structural characters, and the non-standard constants Python accepts.
JSON_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}\[\],]|-?Infinity|NaN')


class SyntaxProblem(Exception):
    def __init__(self, pos, message):
        super().__init__(message)
        self.pos = pos
        self.message = message


def location(text, pos):
    line = text.count("\n", 0, pos) + 1
    return line, pos - text.rfind("\n", 0, pos)


def blank(match):
    return re.sub(r"[^\n]", " ", match.group())


def strip_jsonc(text):
    """Blank out comments and trailing commas, keeping every line and column."""

    def replace(m):
        if m.group("unclosed"):
            raise SyntaxProblem(m.start(), "unterminated /* comment")
        return m.group() if m.group("string") else blank(m)

    return JSONC_TOKEN.sub(replace, text)


def suspects(text):
    """Yield (pos, message) for duplicate keys and NaN/Infinity in parsed JSON."""
    stack = []  # one set of seen keys per open object, None per open array
    expect_key = False
    for m in JSON_TOKEN.finditer(text):
        tok = m.group()
        if tok[0] == '"':
            if expect_key:
                key = json.loads(tok)
                if key in stack[-1]:
                    yield m.start(), f"duplicate key {tok}"
                stack[-1].add(key)
                expect_key = False
        elif tok == "{":
            stack.append(set())
            expect_key = True
        elif tok == "[":
            stack.append(None)
        elif tok in "}]":
            stack.pop()
            expect_key = False
        elif tok == ",":
            expect_key = stack[-1] is not None
        else:
            yield m.start(), f"{tok} is not valid JSON"


def check_json(text, jsonc):
    if text.startswith(BOM):
        if not jsonc:
            yield 0, "byte order mark at start of file (not allowed in JSON)"
        text = " " + text[1:]
    if jsonc:
        text = strip_jsonc(text)

    # Python's parser keeps the last of duplicate keys and accepts NaN and
    # Infinity, so note them here and locate them with a rescan.
    suspect = False

    def object_pairs(pairs):
        nonlocal suspect
        suspect = suspect or len({key for key, _ in pairs}) != len(pairs)
        return pairs

    def constant(name):
        nonlocal suspect
        suspect = True

    try:
        json.loads(text, object_pairs_hook=object_pairs, parse_constant=constant)
    except json.JSONDecodeError as e:
        hint = ""
        if not jsonc:
            try:
                json.loads(strip_jsonc(text))
                hint = " (comments and trailing commas are allowed only in JSONC files)"
            except (ValueError, SyntaxProblem):
                pass
        yield e.pos, f"invalid {'JSONC' if jsonc else 'JSON'}: {e.msg}{hint}"
        return
    if suspect:
        yield from suspects(text)


def check_toml(text):
    if text.startswith(BOM):
        yield 0, "byte order mark at start of file (not allowed in TOML)"
        text = " " + text[1:]
    try:
        tomli.loads(text)
    except tomli.TOMLDecodeError as e:
        yield e.pos, f"invalid TOML: {e.msg}"


def check_file(path, kind):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"{path}: {e.strerror}")
        return False
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        text = data[: e.start].decode("utf-8")
        line, col = location(text, len(text))
        print(f"{path}:{line}:{col}: not valid UTF-8")
        return False
    try:
        problems = list(check_toml(text) if kind == "toml" else check_json(text, kind == "jsonc"))
    except SyntaxProblem as e:
        problems = [(e.pos, e.message)]
    for pos, message in problems:
        line, col = location(text, pos)
        print(f"{path}:{line}:{col}: {message}")
    return not problems


def main(argv):
    if len(argv) < 1 or argv[0] not in ("json", "jsonc", "toml"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    kind, paths = argv[0], argv[1:]
    results = [check_file(path, kind) for path in paths]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
