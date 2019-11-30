# -*- coding: utf-8 -*-
import io

from setuptools import setup

with io.open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="telemetry",
    version="0.0.1",
    description="Profiling in production",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Andrey Avdeev",
    author_email="seorazer@gmail.com",
    license="Apache 2.0",
    packages=["telemetry"],
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=["loguru>=0.3.2", "statsd>=3.3.0"],
    keywords="statsd telemetry",
    url="https://github.com/andrey-avdeev/telemetry",
    download_url='https://github.com/andrey-avdeev/telemetry/archive/v_0.0.1.tar.gz'
)
