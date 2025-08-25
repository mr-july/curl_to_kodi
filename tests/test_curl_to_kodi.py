import re
from curl_to_kodi.cli import parse_curl, kodi_strm_content, sanitize_filename, construct_yt_dlp_args

def test_parse_basic_url_and_headers():
    cmd = "curl 'https://example.com/v.mp4' -H 'User-Agent: UA' -H \"Referer: https://ref\" -H cookie: a=b"
    url, headers = parse_curl(cmd)
    assert url == "https://example.com/v.mp4"
    # Only whitelisted headers are kept by default
    assert "User-Agent" in headers or "user-agent" in {k.lower() for k in headers}
    assert "Referer" in headers or "referer" in {k.lower() for k in headers}
    assert "cookie" in {k.lower() for k in headers}


def test_kodi_strm_content():
    url = "https://example.com/vid.mp4"
    headers = {"User-Agent": "UA/1.0", "Referer": "https://ref"}
    s = kodi_strm_content(url, headers)
    assert s.startswith(url + "|")
    assert "User-Agent=" in s and "Referer=" in s

def test_sanitize_filename():
    assert sanitize_filename("bad:name*here?.mp4") == "bad_name_here_"
    assert sanitize_filename("") == "output"

def test_construct_yt_dlp_args():
    args = construct_yt_dlp_args("https://ex", {"H": "V"}, "out")
    assert args[0] == "yt-dlp"
    assert "--add-header" in args and "H: V" in args
    assert "-o" in args and "out.%(ext)s" in args


def test_parse_unquoted_header_no_space():
    cmd = "curl https://example.com -H X-Token:abc"
    url, headers = parse_curl(cmd, include_all_headers=True)
    assert url == "https://example.com"
    assert headers["X-Token"] == "abc"
