# OpenInCode

<p>Simple script to open <a href="https://code.visualstudio.com/">VS Code</a> from Nautilus (Gnome Files) Menu</p>

## Dependency

`nautilus-python`( `python-nautilus` on Debian/Ubuntu based)

### Ubuntu

```bash
sudo apt install python3-nautilus
```

### Fedora

```bash
sudo dnf install nautilus-python
```

## Installation

### Arch Linux

Install from AUR

```bash
yay -S nautilus-open-in-code
```

Restart Nautilus

```bash
nautilus -q
```

### Other Disto

Clone this repository and use the install script.

```bash
git clone -b open-in-code https://github.com/GustavoWidman/nautilus-open-in-ptyxis.git
cd nautilus-open-in-ptyxis
sudo ./install.sh
```
