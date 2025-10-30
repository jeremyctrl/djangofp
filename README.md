<div align="center">

# djangofp

<a href="https://pypi.org/project/djangofp/"><img src="https://img.shields.io/pypi/v/djangofp.svg" alt="PyPI"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>

Simple Django static-asset version probe.

</div>

`djangofp` fetches Django's admin CSS assets from a target site, fingerprints them by size and SHA256, and compares them against a local signature database.  

This helps identify the Django version, or narrow down candidates, based on unique static asset fingerprints.

## How It Works

`djangofp` requests the Django admin CSS files from the target site, computes SHA256 and size fingerprints, and compares them against a built-in database of known Django releases.

The fingerprint database currently covers Django versions **4.1.x through 5.2.7** (latest release).  

> Admin CSS assets used for matching were introduced in Django 4.1 and do not exist in earlier versions.

## Installation

You can install `djangofp` using [pipx](https://pypa.github.io/pipx):

```bash
pipx install djangofp
```

## Usage

```bash
djangofp https://example.com
```

### Example

```bash
$ djangofp https://example.com

[+] base: size=22154 sha256=2374a875...
[+] forms: size=8525 sha256=bccb52c9...
[+] dashboard: size=441 sha256=882cfb2a...
[+] responsive: size=16632 sha256=890d9ac7...
[+] exact match: 18894b0...
        versions: 5.2
```