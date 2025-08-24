# curl-to-kodi

Convert `curl` command lines (with headers) to Kodi `.strm` files and yt-dlp shell scripts.

## Features

- Parse curl command to extract URL and allowed headers.
- Generate Kodi `.strm` files compatible with custom headers.
- Generate a ready-to-run `yt-dlp` shell script, preserving allowed headers and using your specified stream title for output.
- Can read curl command directly from your clipboard.
- Command-line options for custom output names and stream titles.

## Installation

> This project uses [uv](https://github.com/astral-sh/uv) for Python dependency management.

```sh
uv venv
uv pip install -e .
```

## Usage

### Basic: Convert curl to Kodi .strm

```sh
curl-to-kodi "curl 'https://example.com/video.mp4' -H 'Authorization: Bearer TOKEN'" --title "My Stream"
```

Creates `My Stream.strm`.

### Use clipboard as input

Copy your curl command, then run:

```sh
curl-to-kodi --title "Copied Stream"
```

### Specify custom output name

```sh
curl-to-kodi "curl ... " -o custom_name
```

Creates `custom_name.strm`.

### Generate yt-dlp shell script

```sh
curl-to-kodi "curl ... " --yt-dlp --title "My Stream"
```

Creates both `My Stream.strm` and `My Stream.sh` (the shell script contains the yt-dlp command).

### Example yt-dlp command

The generated shell script will look like:

```sh
#!/bin/sh
yt-dlp --add-header "Authorization: Bearer TOKEN" "https://example.com/video.mp4" -o "My Stream.%(ext)s"
```

## Testing

Tests are in the `tests/` directory and use `pytest`.

Run tests with:

```sh
uv pip install pytest
pytest
```

## License

MIT
