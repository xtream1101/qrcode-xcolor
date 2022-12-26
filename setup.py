from setuptools import find_packages, setup

try:
    with open("README.md", "r") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ""

setup(
    name="qrcode-xcolor",
    packages=find_packages(),
    version="0.1.1",
    license="MIT",
    description="Custom QRCode Modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xtream1101/qrcode-xcolor",
    install_requires=[
        "qrcode[pil]",
    ],
)
