#!/usr/bin/env python3
"""Rewrite a built sdist into a byte-reproducible one.

`python -m build --sdist` honours SOURCE_DATE_EPOCH for the ustar mtime field but still emits
a PAX extended header carrying the real sub-second file mtime, and gzip stamps its own header
mtime, so two sdist builds differ byte-for-byte even though their contents are identical. This
repacks the archive deterministically: sorted member order, fixed integer mtime (so no PAX
mtime record is emitted), zeroed uid/gid/uname/gname, USTAR format, and gzip with mtime=0.

Usage:  SOURCE_DATE_EPOCH=<epoch> python repack_sdist.py dist/<name>.tar.gz
Rewrites the file in place. Idempotent and environment-independent given the same inputs.
"""
from __future__ import annotations

import gzip
import io
import os
import sys
import tarfile

EPOCH = int(os.environ.get("SOURCE_DATE_EPOCH", "1735689600"))


def repack(path: str) -> None:
    with tarfile.open(path, "r:*") as tf:
        entries = []
        for m in tf.getmembers():
            payload = tf.extractfile(m).read() if m.isfile() else None
            entries.append((m, payload))

    inner = io.BytesIO()
    with tarfile.open(fileobj=inner, mode="w", format=tarfile.USTAR_FORMAT) as out:
        for m, payload in sorted(entries, key=lambda e: e[0].name):
            ti = tarfile.TarInfo(name=m.name)
            ti.size = m.size
            ti.mtime = EPOCH            # integer -> fits ustar -> no PAX mtime record
            ti.mode = m.mode
            ti.type = m.type
            ti.linkname = m.linkname
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = ""
            out.addfile(ti, io.BytesIO(payload) if payload is not None else None)

    with open(path, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:  # mtime=0 -> no gzip timestamp
            gz.write(inner.getvalue())


if __name__ == "__main__":
    repack(sys.argv[1])
    print(f"repacked deterministically (SOURCE_DATE_EPOCH={EPOCH}): {sys.argv[1]}")
