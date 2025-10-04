# djangofp

Simple Django static-asset version probe.

`djangofp` fetches Django's admin CSS assets from a target site, fingerprints them by size and SHA256, and compares them against a signature database. This can help identify the Django version (or narrow down candidates).

## Usage

```bash
djangofp https://example.com
```