from __future__ import annotations

import argparse
import os
import platform
import re
import shlex
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

try:
    import pyperclip  # type: ignore
except Exception:  # pragma: no cover - only used at runtime
    pyperclip = None  # type: ignore

_ALLOWED_HEADERS = {
    "cookie",
    "origin",
    "referer",
    "user-agent",
}

_URL_PATTERN = re.compile(r"""['"]?(https?://[^\s'"]+)['"]?""")
_HEADER_PATTERN = re.compile(
    r"(?:^|\s)(?:-H|--header)\s+(?:'([^']+)'|\"([^\"]+)\"|([^\s]+))",
    re.IGNORECASE,
)

def parse_curl(curl_command: str,
               *,
               allowed_headers: Optional[Iterable[str]] = None,
               include_all_headers: bool = False) -> Tuple[Optional[str], Dict[str, str]]:
    """Extract the first URL and headers from a curl command."""
    url_match = _URL_PATTERN.search(curl_command)
    url = url_match.group(1) if url_match else None

    headers: Dict[str, str] = {}
    allow = set(h.lower() for h in (allowed_headers or _ALLOWED_HEADERS))
    for h1, h2, h3 in _HEADER_PATTERN.findall(curl_command):
        raw = h1 or h2 or h3
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        k = key.strip()
        v = value.strip()
        if include_all_headers or k.lower() in allow:
            headers[k] = v
    return url, headers

def kodi_strm_content(url: str, headers: Dict[str, str]) -> str:
    """Compose the .strm content for Kodi: 'url|k=v&k2=v2' (values URL-encoded)."""
    if not url:
        raise ValueError("No URL found in curl command.")
    if headers:
        header_str = "|" + "&".join(f"{k}={quote(v)}" for k, v in headers.items())
        return f"{url}{header_str}"
    return url

_INVALID_FILENAME_CHARS = re.compile(r"[\\/*?:\"<>|]\s*")



def sanitize_filename(name: str) -> str:
    base = os.path.splitext(name)[0]
    cleaned = re.sub(r'[\/*?:"<>|]', "_", base)
    return cleaned if cleaned else "output"

def construct_yt_dlp_args(url: str, headers: Dict[str, str], output_name: Optional[str]) -> List[str]:
    args: List[str] = ["yt-dlp"]
    for k, v in headers.items():
        args.extend(["--add-header", f"{k}: {v}"])
    args.append(url)
    if output_name:
        args.extend(["-o", f"{output_name}.%(ext)s"])
    return args

def _sh_join(args: List[str]) -> str:
    try:
        return shlex.join(args)
    except Exception:  # pragma: no cover
        return " ".join(shlex.quote(a) for a in args)

def _bat_join(args: List[str]) -> str:
    def q(a: str) -> str:
        if not a:
            return '""'
        if any(c.isspace() for c in a) or any(c in a for c in '()%!^&<>|,;'):
            return '"' + a.replace('"', '""') + '"'
        return a
    return " ".join(q(a) for a in args)

def _ps1_join(args: List[str]) -> str:
    def q(a: str) -> str:
        if a == "":
            return "''"
        if re.search(r"\s|[()!^&<>|,;]", a):
            return "'" + a.replace("'", "''") + "'"
        return a
    return " ".join(q(a) for a in args)

def write_shell_script(filename: Path, args: List[str], fmt: str = "sh") -> None:
    fmt = fmt.lower()
    filename = filename.with_suffix({
        "sh": ".sh",
        "bat": ".bat",
        "ps1": ".ps1",
    }.get(fmt, ".sh"))

    if fmt == "bat":
        content = _bat_join(args)
        text = f"@echo off\n{content}\n"
    elif fmt == "ps1":
        content = _ps1_join(args)
        text = f"# PowerShell script\n{content}\n"
    else:
        content = _sh_join(args)
        text = f"#!/bin/sh\n{content}\n"

    filename.write_text(text, encoding="utf-8")
    if fmt == "sh":
        try:
            os.chmod(filename, 0o755)
        except Exception:
            pass

def guess_default_script_format() -> str:
    sysname = platform.system().lower()
    if "windows" in sysname:
        return "bat"
    return "sh"

def get_curl_from_clipboard() -> str:
    if pyperclip is None:
        raise ImportError("pyperclip is required for clipboard support. Install it with 'pip install pyperclip'.")
    text = pyperclip.paste()  # type: ignore[attr-defined]
    if not text or not text.strip():
        raise ValueError("Clipboard is empty; provide a curl command or copy one first.")
    return text

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a curl command to a Kodi .strm file and optional yt-dlp script. "
            "If no curl command is provided, the clipboard is used."
        )
    )
    parser.add_argument("curl_command", nargs="?", help="The curl command to parse. If omitted, reads from clipboard.")
    parser.add_argument("-t", "--title", help="Stream title (used as base output name; .strm and script extension will be appended).")
    parser.add_argument("-o", "--output", help="Base output name for files (ignored if --title is provided).")
    parser.add_argument("--yt-dlp", action="store_true", help="Emit a yt-dlp script and print the command.")
    parser.add_argument("--all-headers", action="store_true", help="Include all headers from the curl command (ignore whitelist).")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be written without creating files.")
    parser.add_argument("--script-format", choices=["sh", "bat", "ps1"], default=guess_default_script_format(), help="Format of the generated script when --yt-dlp is used.")
    args = parser.parse_args(argv)

    try:
        curl_cmd = args.curl_command if args.curl_command else get_curl_from_clipboard()
        if not args.curl_command:
            print("Read curl command from clipboard.")

        url, headers = parse_curl(curl_cmd, include_all_headers=args.all_headers)
        if not url:
            parser.error("Could not find a valid URL in the provided curl command.")

        if not headers and not args.all_headers:
            print("Note: No whitelisted headers found. Use --all-headers to include all provided headers.", file=sys.stderr)

        base_output_raw = args.title or args.output or "output"
        base_output = sanitize_filename(base_output_raw)

        strm_content = kodi_strm_content(url, headers)
        strm_path = Path(f"{base_output}.strm")

        print("Generated .strm content:")
        print(strm_content)

        if not args.dry_run:
            strm_path.write_text(strm_content, encoding="utf-8")
            print(f".strm file written: {strm_path}")
        else:
            print("(dry-run) .strm file not written")

        if args.yt_dlp:
            yt_args = construct_yt_dlp_args(url, headers, base_output)
            if args.script_format == "bat":
                joined = _bat_join(yt_args)
            elif args.script_format == "ps1":
                joined = _ps1_join(yt_args)
            else:
                joined = _sh_join(yt_args)

            print("yt-dlp command:")
            print(joined)

            if not args.dry_run:
                script_path = Path(base_output)
                write_shell_script(script_path, yt_args, fmt=args.script_format)
                print(f"yt-dlp script written: {script_path.with_suffix('.' + args.script_format)}")
            else:
                print("(dry-run) script not written")

        return 0

    except (ValueError, ImportError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Aborted by user.", file=sys.stderr)
        return 130

def entrypoint() -> None:
    sys.exit(main())
