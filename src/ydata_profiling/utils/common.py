"""Common util functions (e.g. missing in Python)."""
import collections.abc
import os
import platform
import subprocess
import zipfile
from datetime import datetime, timedelta

# Monkeypatch bug in imagehdr
from imghdr import tests
from pathlib import Path
from typing import Mapping

import pandas as pd
import requests

from ydata_profiling.version import __version__


def update(d: dict, u: Mapping) -> dict:
    """Recursively update a dict.

    Args:
        d: Dictionary to update.
        u: Dictionary with values to use.

    Returns:
        The merged dictionary.
    """
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def _copy(self, target):
    """Monkeypatch for pathlib

    Args:
        self:
        target:

    Returns:

    """
    import shutil

    assert self.is_file()
    shutil.copy(str(self), target)


Path.copy = _copy  # type: ignore


def extract_zip(outfile, effective_path):
    try:
        with zipfile.ZipFile(outfile) as z:
            z.extractall(effective_path)
    except zipfile.BadZipFile as e:
        raise ValueError("Bad zip file") from e


def test_jpeg1(h, f):
    """JPEG data in JFIF format"""
    if b"JFIF" in h[:23]:
        return "jpeg"


JPEG_MARK = (
    b"\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06"
    b"\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f"
)


def test_jpeg2(h, f):
    """JPEG with small header"""
    if len(h) >= 32 and h[5] == 67 and h[:32] == JPEG_MARK:
        return "jpeg"


def test_jpeg3(h, f):
    """JPEG data in JFIF or Exif format"""
    if h[6:10] in (b"JFIF", b"Exif") or h[:2] == b"\xff\xd8":
        return "jpeg"


tests.append(test_jpeg1)
tests.append(test_jpeg2)
tests.append(test_jpeg3)


def convert_timestamp_to_datetime(timestamp: int) -> datetime:
    if timestamp >= 0:
        return datetime.fromtimestamp(timestamp)
    else:
        return datetime(1970, 1, 1) + timedelta(seconds=int(timestamp))


def analytics_features(dataframe, datatype: bool, report_type: bool):
    endpoint = "https://packages.ydata.ai/ydata-profiling?"

    if os.getenv("YDATA_PROFILING_NO_ANALYTICS") != True:
        package_version = __version__
        try:
            subprocess.check_output("nvidia-smi")
            gpu_present = True
        except Exception:
            gpu_present = False

        python_version = ".".join(platform.python_version().split(".")[:2])

        try:
            request_message = (
                f"{endpoint}version={package_version}"
                f"&python_version={python_version}"
                f"&report_type={report_type}"
                f"&dataframe={dataframe}"
                f"&datatype={datatype}"
                f"&os={platform.system()}"
                f"&gpu={str(gpu_present)}"
            )

            requests.get(request_message)
        except Exception:
            pass
