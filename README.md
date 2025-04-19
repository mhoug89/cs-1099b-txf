# cs-1099b-txf

This repo is a fork of mssb-1099b-txf (which works with Morgan Stanley
1099-B PDFs) that has been modified to work with a subset of Charles Schwab
1099-B PDFs. I've made minor adjustments to account for the different PDF
layout (and thus the different layout of the converted text). The goal of
this tool is to convert simple Charles Schwab 1099-B PDFs to TXF files that
can be imported into TurboTax. The goal is to *reduce* data entry, not to
completely automate the process, meaning that you'll need to manually verify
and potentially modify the entries in TurboTax (or your tax preparation
software of choice) after importing the TXF file.

WARNING: I have only tested this with my own personal 1099-B PDFs; there are
all sorts of edge cases and fields that I don't handle properly here. The tool
has been used to import only a few different 1099-Bs so you may encounter
errors. But, for my own purposes -- processing my 1099-B that covers selling
RSUs from my employer -- this has worked for me. Your mileage may vary; use at
your own risk, and always be sure to manually validate your results against the
1099-B you used as input!

## What is TXF?

The TXF format is relatively straightforward and text based. It's defined at
https://taxdataexchange.org/docs/txf/v042/index.html

## Usage

```
# Verify pdftotext is installed; if not, see section below.
which pdftotext

python3 cs_1099b_to_txf.py ~/Downloads/1099-B.pdf > ~/1099b.txf
```

After you've generated `1099b.txf`:
- import it into TurboTax
- **DOUBLE-CHECK YOUR RESULTS and verify your entries match your 1099-B!**

## Installation

This script has been tested and run only on Linux. You could, in theory, run it
on a Windows system, but I haven't tried installing all the necessary
dependencies on Windows.

This script has two requirements:
- You have `python3` installed and in your PATH
- You have `pdftotext` installed and in your PATH

`pdftotext` is an executable from [Poppler](https://poppler.freedesktop.org/).
According to the author of the repository this one was forked from, installing
Poppler used to be fairly easy, i.e. via installing the `poppler-utils` package
using your disto's package manager. However, at time of writing (April 2025), I
had to install several dependencies, both via manual download and install, and
via my package manager.

### pdttotext installation on Ubuntu 22.04.5

The instructions below are the steps I had to follow on my WSL (Windows
Subsystem for Linux) instance running Ubuntu 22.04.5 LTS in order to get
`pdftotext` installed.

#### 1. Download and install gpgme-1.19.0

```
cd ~
mkdir -p repos/
cd repos/
wget -O gpgme-1.19.0.tar.bz2 "https://www.gnupg.org/ftp/gcrypt/gpgme/gpgme-1.19.0.tar.bz2"
tar -xf gpgme-1.19.0.tar.bz2
cd gpgme-1.19.0/
./configure
make
sudo make install
```

#### 2. Install Poppler dependencies via apt

```
sudo apt install \
    libassuan-dev \
    libcurlpp-dev
    libfontconfig-dev \
    libfreetype-dev \
    libgpg-error-dev \
    libgpgmepp6 \
    libgpgmepp-dev \
    liblcms2-dev \
    libnss3-dev \
    libopenjp2-7-dev \
    libqt6core6 \
    libqt6core5compat6-dev \
    libtiff-dev
```

#### 3. Download and install Poppler

```
cd ~
mkdir poppler
cd poppler
wget -O poppler-25.04.0.tar.xz "https://poppler.freedesktop.org/poppler-25.04.0.tar.xz"
tar -xf poppler-25.04.0.tar.xz
cd poppler-25.04.0/
mkdir build/
cd build/
cmake .. ENABLE_BOOST=OFF
make
sudo make install

which pdftotext  # Should find pdftotext now that poppler is installed!
```

