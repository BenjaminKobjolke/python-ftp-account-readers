# python-ftp-account-readers

Read saved FTP, FTPS, and SFTP sites from WinSCP, FileZilla, and Notepad++ NppFTP. This package
contains readers only; it does not modify the source applications' settings.

## Install

```sh
uv add "python-ftp-account-readers @ git+https://github.com/BenjaminKobjolke/python-ftp-account-readers.git@v0.1.0"
```

## Usage

```python
from ftp_account_readers import read_filezilla, read_nppftp, read_winscp

accounts = read_filezilla() + read_nppftp() + read_winscp()
for account in accounts:
    print(account.describe())
```

You can pass an explicit `Path` to `read_filezilla(path)` or `read_nppftp(path)`. The matching
`is_filezilla_available(path)` and `is_nppftp_available(path)` functions accept the same optional
`Path` and check that location. Their defaults are `%APPDATA%/FileZilla/sitemanager.xml` and
`%APPDATA%/Notepad++/plugins/config/NppFTP/NppFTP.xml`.

`read_winscp(sessions_key)` and `is_winscp_available(sessions_key)` accept an optional registry
key relative to `HKEY_CURRENT_USER`. The default is
`Software\Martin Prikryl\WinSCP 2\Sessions` on Windows.

The public API also includes `FtpAccount`, `FtpProtocol`, and the availability checks
`is_winscp_available()`, `is_filezilla_available()`, and `is_nppftp_available()`.

## Limits

- WinSCP reading is Windows-only because sessions are stored in the Windows registry.
- FileZilla master-password protected entries cannot be decrypted; they are returned with an empty
  password and a warning is logged.
- NppFTP passwords encrypted with a user-set master password cannot be decrypted. The default
  built-in key is supported.
- This package does not write accounts back to any application.
