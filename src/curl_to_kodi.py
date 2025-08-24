import re
import sys
import os
from urllib.parse import quote

try:
    import pyperclip
except ImportError:
    pyperclip = None

ALLOWED_HEADERS = {
    'cookie',
    'origin',
    'referer',
    'user-agent',
}

def parse_curl(curl_command):
    url_match = re.search(r"(https?://[^\s'\"]+)", curl_command)
    headers = re.findall(r"-H\s+'([^']+)'|-H\s+\"([^\"]+)\"", curl_command)
    result_headers = {}
    for h1, h2 in headers:
        header = h1 if h1 else h2
        if ':' in header:
            key, value = header.split(':', 1)
            key_stripped = key.strip()
            if key_stripped.lower() in ALLOWED_HEADERS:
                result_headers[key_stripped] = value.strip()
    url = url_match.group(1) if url_match else None
    return url, result_headers

def kodi_strm_content(url, headers):
    if not url:
        raise ValueError("No URL found in curl command.")
    if headers:
        header_str = '|'
        header_str += '&'.join(f"{k}={quote(v)}" for k, v in headers.items())
        return f"{url}{header_str}"
    else:
        return url

def get_curl_from_clipboard():
    if pyperclip is None:
        raise ImportError("pyperclip is required for clipboard support. Install it with 'pip install pyperclip'.")
    return pyperclip.paste()

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def construct_yt_dlp_command(url, headers, output_name):
    cmd = ["yt-dlp"]
    if headers:
        for k, v in headers.items():
            cmd.append("--add-header")
            cmd.append(f"{k}: {v}")
    cmd.append(url)
    if output_name:
        safe_output = sanitize_filename(output_name)
        cmd.append("-o")
        cmd.append(f"{safe_output}.%(ext)s")
    return ' '.join(f'"{part}"' if ' ' in part else part for part in cmd)

def write_shell_script(filename, command):
    with open(filename, 'w') as f:
        f.write("#!/bin/sh\n")
        f.write(command + "\n")
    os.chmod(filename, 0o755)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert a curl command to a Kodi .strm file and yt-dlp command.")
    parser.add_argument("curl_command", nargs="?", help="The curl command to parse. If omitted, reads from clipboard.")
    parser.add_argument("-t", "--title", help="Stream title (used as output file name; .strm and .sh will be appended).")
    parser.add_argument("-o", "--output", help="Base output name for .strm and .sh files (ignored if --title is provided).")
    parser.add_argument("--yt-dlp", action="store_true", help="Write yt-dlp shell script and print command.")
    args = parser.parse_args()

    if args.curl_command:
        curl_command = args.curl_command
    else:
        curl_command = get_curl_from_clipboard()
        print("Read curl command from clipboard.")

    url, headers = parse_curl(curl_command)
    strm_content = kodi_strm_content(url, headers)

    if args.title:
        base_output = sanitize_filename(args.title)
    elif args.output:
        base_output = sanitize_filename(args.output)
    else:
        base_output = "output"

    strm_filename = base_output + ".strm"
    with open(strm_filename, 'w') as f:
        f.write(strm_content)
    print(f".strm file generated: {strm_filename}")

    if args.yt_dlp:
        yt_dlp_cmd = construct_yt_dlp_command(url, headers, base_output)
        print("yt-dlp command:")
        print(yt_dlp_cmd)
        sh_filename = base_output + ".sh"
        write_shell_script(sh_filename, yt_dlp_cmd)
        print(f"yt-dlp shell script written: {sh_filename}")

if __name__ == "__main__":
    main()
