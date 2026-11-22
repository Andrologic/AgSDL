"""Bounded reading of ordinary ZIP32 members."""

import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

TOOLING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLING))
from agsdl.archive_zip import CHUNK, member_ends, read_member


class StreamingOutput(io.BytesIO):
    def seekable(self):
        return False

    def seek(self, *args):
        raise io.UnsupportedOperation("not seekable")


class BoundedTarget(io.BytesIO):
    def write(self, data):
        if len(data) > CHUNK:
            raise AssertionError("unbounded output block")
        return super().write(data)


class ArchiveZipTest(unittest.TestCase):
    def test_stored_and_deflated_members(self):
        contents = {
            "empty": b"",
            "project/é.txt": (b"AgSDL project\n" * 20000),
            "project/bytes.bin": bytes(range(256)) * 700,
        }
        for method in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            for stream in (io.BytesIO(), StreamingOutput()):
                with self.subTest(method=method, descriptor=isinstance(stream, StreamingOutput)):
                    with zipfile.ZipFile(stream, "w", compression=method, allowZip64=False) as archive:
                        for name, data in contents.items():
                            archive.writestr(name, data)
                    with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
                        infos = archive.infolist()
                        ends = member_ends(archive)
                        for first, second in zip(infos, infos[1:]):
                            self.assertEqual(ends[first.header_offset], second.header_offset)
                        # Read in reverse order to exercise the member offsets.
                        for info in reversed(infos):
                            data = contents[info.filename]
                            for factory in (BoundedTarget, tempfile.TemporaryFile):
                                with factory() as target:
                                    result = read_member(archive, info, target, ends[info.header_offset])
                                    target.seek(0)
                                    self.assertEqual(target.read(), data)
                                    self.assertEqual(result, {"size": len(data),
                                        "sha256": hashlib.sha256(data).hexdigest()})

    def test_duplicate_offsets_are_rejected(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("one", b"one")
        with zipfile.ZipFile(stream) as archive:
            info = archive.infolist()[0]
            with mock.patch.object(archive, "infolist", return_value=[info, info]):
                with self.assertRaisesRegex(zipfile.BadZipFile, "duplicate"):
                    member_ends(archive)


if __name__ == "__main__":
    unittest.main()
