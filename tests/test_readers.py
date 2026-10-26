import sys
from pathlib import Path

import pytest

from ftp_account_readers import FtpProtocol, read_filezilla, read_nppftp

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


def test_winscp_module_imports_without_winreg_and_availability_is_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "winreg", None)
    from ftp_account_readers import winscp

    assert winscp.is_winscp_available() is False
