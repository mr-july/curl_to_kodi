# curl-to-kodi

Convert a `curl` command into a Kodi `.strm` entry and optionally generate a `yt-dlp` script with the same headers.

## Features

- Parses `-H/--header` (quoted or unquoted) and extracts the URL (quoted or unquoted).
- Whitelists common headers required by Kodi/yt-dlp (`cookie`, `origin`, `referer`, `user-agent`) with an option to include all headers.
- Generates `.strm` files where headers are appended as `|k=v&k2=v2` with URL-encoding for values.
- Optionally creates a platform-appropriate script for `yt-dlp` (`.sh` on Unix, `.bat` on Windows, `.ps1` for PowerShell).
- Clipboard input supported if `pyperclip` is installed.
- Helpful flags: `--dry-run`, `--all-headers`, `--script-format {sh,bat,ps1}`.

## Quickstart (using `uv`)

```bash
# Create and activate a virtualenv
uv venv
source .venv/bin/activate  # (On Windows: .venv\Scripts\activate)

# Install in editable mode
uv pip install -e .

# Optional: clipboard support
uv pip install '.[clipboard]'

# Run
curl-to-kodi \  "curl 'https://example.com/video.mp4' -H 'User-Agent: UA' -H 'Referer: https://ref.example'" \  --yt-dlp --title "My Stream"
```

## CLI

```
usage: curl-to-kodi [-h] [-t TITLE] [-o OUTPUT] [--yt-dlp] [--all-headers]
                    [--dry-run] [--script-format {sh,bat,ps1}]
                    [curl_command]
```

- `curl_command`: If omitted, reads from clipboard (requires `pyperclip`).  
- `-t/--title`: Stream title used as base output name.  
- `-o/--output`: Base output name (ignored if `--title` given).  
- `--yt-dlp`: Emit a script with a `yt-dlp` command and print it to the console.  
- `--all-headers`: Include every header from the curl command (bypasses whitelist).  
- `--dry-run`: Show outputs without writing files.  
- `--script-format`: `sh` (default on Unix), `bat` (default on Windows), or `ps1`.

## Examples

```bash
# Read from clipboard and create .strm
curl-to-kodi

# Provide curl inline, include all headers, no file writes
curl-to-kodi "curl https://example/file.mp4 -H 'X-Foo: bar'" --all-headers --dry-run

# Force PowerShell script output
curl-to-kodi "curl https://example/file.mp4" --yt-dlp --script-format ps1
```

## Development

```bash
# Install dev tools
uv pip install -e .
uv pip install pytest

# Run tests
pytest
```
