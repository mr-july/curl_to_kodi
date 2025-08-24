import pytest
import os
import src.curl_to_kodi as ctk

CURL_EXAMPLE = "curl 'https://example.com/video.mp4' -H 'Authorization: Bearer TOKEN' -H 'User-Agent: Kodi/19' -H 'Other: value'"

def test_parse_curl_filters_headers():
    url, headers = ctk.parse_curl(CURL_EXAMPLE)
    assert url == "https://example.com/video.mp4"
    assert "Authorization" in headers
    assert "User-Agent" in headers
    assert "Other" not in headers

def test_kodi_strm_content():
    url, headers = ctk.parse_curl(CURL_EXAMPLE)
    content = ctk.kodi_strm_content(url, headers)
    assert content.startswith(url)
    assert "|Authorization=Bearer TOKEN&User-Agent=Kodi/19" in content

def test_sanitize_filename():
    unsafe = 'Movie: "Best/Stream?"'
    safe = ctk.sanitize_filename(unsafe)
    assert all(c not in safe for c in '\\/*?:"<>|')

def test_construct_yt_dlp_command():
    url, headers = ctk.parse_curl(CURL_EXAMPLE)
    cmd = ctk.construct_yt_dlp_command(url, headers, "TestStream")
    assert "yt-dlp" in cmd
    assert '--add-header' in cmd
    assert 'Authorization:' in cmd
    assert '-o' in cmd
    assert "TestStream.%(ext)s" in cmd

def test_write_shell_script(tmp_path):
    script_path = tmp_path / "test.sh"
    ctk.write_shell_script(str(script_path), 'echo hello')
    assert script_path.exists()
    with open(script_path, 'r') as f:
        assert 'echo hello' in f.read()

def test_main_strm_and_sh(tmp_path, monkeypatch):
    # Patch sys.argv to simulate command line
    curl_cmd = "curl 'https://example.com/vid.mp4' -H 'Authorization: TOKEN'"
    monkeypatch.setattr('sys.argv', ['curl-to-kodi', curl_cmd, '--title', 'TestOutput', '--yt-dlp'])
    monkeypatch.setattr('os.getcwd', lambda: str(tmp_path))
    ctk.main()
    assert os.path.exists(os.path.join(os.getcwd(), 'TestOutput.strm'))
    assert os.path.exists(os.path.join(os.getcwd(), 'TestOutput.sh'))
    # Clean up
    os.remove(os.path.join(os.getcwd(), 'TestOutput.strm'))
    os.remove(os.path.join(os.getcwd(), 'TestOutput.sh'))

def test_clipboard(monkeypatch):
    # Patch pyperclip.paste
    monkeypatch.setattr(ctk, 'pyperclip', type('DummyClip', (), {'paste': lambda: CURL_EXAMPLE}))
    url, headers = ctk.parse_curl(ctk.get_curl_from_clipboard())
    assert url == "https://example.com/video.mp4"
