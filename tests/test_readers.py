from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from ftp_account_readers import (
    FtpProtocol,
    is_filezilla_available,
    is_nppftp_available,
    read_filezilla,
    read_nppftp,
)
from ftp_account_readers import constants as c


class _FakeKey:
    def __init__(self) -> None:
        self.values: dict[str, str | int] = {}
        self.subkeys: dict[str, _FakeKey] = {}

    def __enter__(self) -> _FakeKey:
        return self

    def __exit__(self, *args: object) -> None:
        pass


@pytest.fixture
def fake_winreg(monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    root = _FakeKey()

    def open_key(parent: _FakeKey, subkey: str) -> _FakeKey:
        try:
            return parent.subkeys[subkey]
        except KeyError as error:
            raise FileNotFoundError(subkey) from error

    def query_value_ex(key: _FakeKey, name: str) -> tuple[str | int, int]:
        try:
            return key.values[name], 0
        except KeyError as error:
            raise FileNotFoundError(name) from error

    fake = types.SimpleNamespace(
        HKEY_CURRENT_USER=root,
        OpenKey=open_key,
        CloseKey=lambda key: None,
        EnumKey=lambda key, index: list(key.subkeys)[index],
        QueryInfoKey=lambda key: (len(key.subkeys), len(key.values), 0),
        QueryValueEx=query_value_ex,
    )
    monkeypatch.setitem(sys.modules, "winreg", fake)
    return fake


def _add_winscp_session(registry: types.SimpleNamespace, key: str) -> None:
    sessions = _FakeKey()
    registry.HKEY_CURRENT_USER.subkeys[key] = sessions
    session = _FakeKey()
    session.values.update(
        {
            c.WINSCP_HOST: "ftp.example",
            c.WINSCP_USER: "alice",
            c.WINSCP_PORT: 2121,
            c.WINSCP_FS_PROTOCOL: c.WINSCP_FS_FTP,
        }
    )
    sessions.subkeys["Clients/Site%20W"] = session
    sessions.subkeys[c.WINSCP_DEFAULT_SETTINGS_SESSION] = _FakeKey()


FILEZILLA_XML = """<?xml version="1.0"?>
<FileZilla3 version="3.70.6" platform="windows">
  <Servers>
    <Folder expanded="1">Clients<Folder>Nested<Server>
      <Host>a.example</Host><Port>2121</Port><Protocol>4</Protocol><Type>0</Type>
      <User>alice</User><Pass encoding="base64">c2VjcmV0</Pass><Logontype>1</Logontype>
      <Name>Site A</Name><RemoteDir>1 0 3 www 4 html</RemoteDir>
    </Server></Folder></Folder>
    <Server><Host>b.example</Host><Port>22</Port><Protocol>1</Protocol>
      <User>bob</User><Name>B</Name></Server>
    <Server><Host>c.example</Host><Protocol>0</Protocol><User>carol</User>
      <Pass encoding="crypt">cipher-text</Pass><Name>C</Name></Server>
  </Servers>
</FileZilla3>
"""

NPPFTP_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<NppFTP><Profiles>
  <Profile name="n1" parent="Clients/Nested" hostname="n.example" port="21" username="nina"
    password="{password}" securityMode="2" initialDir="/srv" />
</Profiles></NppFTP>
"""


def test_filezilla_reader_handles_nested_folders_protocols_and_remote_dir(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sitemanager.xml"
    path.write_text(FILEZILLA_XML, encoding="utf-8")

    a, b, _ = read_filezilla(path)

    assert (a.name, a.folder, a.host, a.port, a.user, a.password) == (
        "Site A",
        "Clients/Nested",
        "a.example",
        2121,
        "alice",
        "secret",
    )
    assert a.protocol is FtpProtocol.FTPS
    assert a.remote_dir == "/www/html"
    assert (b.protocol, b.password, b.folder, b.remote_dir) == (FtpProtocol.SFTP, "", "", "")


def test_filezilla_availability_and_reader_use_explicit_path(tmp_path: Path) -> None:
    path = tmp_path / "custom-sitemanager.xml"
    assert is_filezilla_available(path) is False

    path.write_text(FILEZILLA_XML, encoding="utf-8")

    assert is_filezilla_available(path) is True
    assert read_filezilla(path)[0].host == "a.example"


def test_filezilla_availability_and_reader_keep_default_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert is_filezilla_available() is False

    default_path = tmp_path / c.FILEZILLA_RELATIVE_PATH
    default_path.parent.mkdir(parents=True)
    default_path.write_text(FILEZILLA_XML, encoding="utf-8")

    assert is_filezilla_available() is True
    assert read_filezilla()[0].host == "a.example"


def test_filezilla_master_password_encoding_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "sitemanager.xml"
    path.write_text(FILEZILLA_XML, encoding="utf-8")

    _, _, account = read_filezilla(path)

    assert account.password == ""


def test_nppftp_reader_parses_protocol_and_folder(tmp_path: Path) -> None:
    from ftp_account_readers.nppftp_password import encrypt

    path = tmp_path / "NppFTP.xml"
    path.write_text(NPPFTP_XML.format(password=encrypt("npw")), encoding="utf-8")

    (account,) = read_nppftp(path)

    assert (account.name, account.folder, account.host, account.user, account.password) == (
        "n1",
        "Clients/Nested",
        "n.example",
        "nina",
        "npw",
    )
    assert (account.protocol, account.remote_dir) == (FtpProtocol.FTPS, "/srv")


def test_nppftp_availability_and_reader_use_explicit_path(tmp_path: Path) -> None:
    from ftp_account_readers.nppftp_password import encrypt

    path = tmp_path / "custom-NppFTP.xml"
    assert is_nppftp_available(path) is False

    path.write_text(NPPFTP_XML.format(password=encrypt("npw")), encoding="utf-8")

    assert is_nppftp_available(path) is True
    assert read_nppftp(path)[0].host == "n.example"


def test_nppftp_availability_and_reader_keep_default_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ftp_account_readers.nppftp_password import encrypt

    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert is_nppftp_available() is False

    default_path = tmp_path / c.NPPFTP_RELATIVE_PATH
    default_path.parent.mkdir(parents=True)
    default_path.write_text(NPPFTP_XML.format(password=encrypt("npw")), encoding="utf-8")

    assert is_nppftp_available() is True
    assert read_nppftp()[0].host == "n.example"


def test_winscp_explicit_sessions_key(fake_winreg: types.SimpleNamespace) -> None:
    from ftp_account_readers import winscp

    key = r"Software\Custom\Sessions"
    _add_winscp_session(fake_winreg, key)

    assert winscp.is_winscp_available(key) is True
    (account,) = winscp.read_winscp(key)
    assert (account.name, account.folder, account.host, account.user, account.port) == (
        "Site W",
        "Clients",
        "ftp.example",
        "alice",
        2121,
    )
    assert account.protocol is FtpProtocol.FTP
    assert winscp.is_winscp_available(r"Software\Missing") is False
    assert winscp.is_winscp_available() is False


def test_winscp_default_sessions_key_is_unchanged(fake_winreg: types.SimpleNamespace) -> None:
    from ftp_account_readers import winscp

    _add_winscp_session(fake_winreg, c.WINSCP_SESSIONS_KEY)

    assert winscp.is_winscp_available() is True
    (account,) = winscp.read_winscp()
    assert (account.name, account.host, account.user, account.port) == (
        "Site W",
        "ftp.example",
        "alice",
        2121,
    )


def test_winscp_module_imports_without_winreg_and_availability_is_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "winreg", None)
    from ftp_account_readers import winscp

    assert winscp.is_winscp_available() is False
