"""Read ZIP32 members with bounded decompression and integrity checks."""

import hashlib
import struct
import zipfile
import zlib


CHUNK = 64 * 1024
LOCAL_HEADER = struct.Struct("<4s5H3I2H")


def member_ends(archive):
    """Return each local header's next boundary, after ZIP32 preflight."""
    source = archive.fp
    if source is None:
        raise ValueError("closed ZIP archive")
    source.seek(-22, 2)
    footer = source.read(22)
    if len(footer) != 22 or footer[:4] != b"PK\x05\x06":
        raise zipfile.BadZipFile("missing ZIP footer")
    directory = struct.unpack_from("<I", footer, 16)[0]
    offsets = sorted(item.header_offset for item in archive.infolist())
    if (len(set(offsets)) != len(offsets)
            or any(offset < 0 or offset >= directory for offset in offsets)):
        raise zipfile.BadZipFile("duplicate or invalid local header offset")
    return dict(zip(offsets, offsets[1:] + [directory]))


def read_member(archive, info, target, end):
    """Copy one member to target and return its exact size and SHA-256 digest.

    The caller checks the central directory and the member's size limit first,
    and passes the corresponding boundary from member_ends. No other reader may
    use the ZipFile's underlying stream during this call.
    """
    source = archive.fp
    if source is None:
        raise ValueError("closed ZIP archive")
    if info.header_offset < 0 or info.header_offset + LOCAL_HEADER.size > end:
        raise zipfile.BadZipFile("invalid local header offset")
    source.seek(info.header_offset)
    header = source.read(LOCAL_HEADER.size)
    if len(header) != LOCAL_HEADER.size:
        raise zipfile.BadZipFile("truncated local header")
    (signature, version, flags, method, mod_time, mod_date, crc, compressed,
     size, name_length, extra_length) = LOCAL_HEADER.unpack(header)
    date = info.date_time
    expected_time = (date[3] << 11) | (date[4] << 5) | (date[5] // 2)
    expected_date = ((date[0] - 1980) << 9) | (date[1] << 5) | date[2]
    if (signature != b"PK\x03\x04" or version != (info.extract_version | info.reserved << 8)
            or flags != info.flag_bits or flags & (1 | 0x20 | 0x40) or method != info.compress_type
            or method not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
            or mod_time != expected_time or mod_date != expected_date):
        raise zipfile.BadZipFile("local header does not match ZIP directory")
    if flags & 8:
        if (crc not in (0, info.CRC) or compressed not in (0, info.compress_size)
                or size not in (0, info.file_size)):
            raise zipfile.BadZipFile("local sizes or CRC do not match ZIP directory")
    elif (crc, compressed, size) != (info.CRC, info.compress_size, info.file_size):
        raise zipfile.BadZipFile("local sizes or CRC do not match ZIP directory")
    if source.tell() + name_length + extra_length + info.compress_size > end:
        raise zipfile.BadZipFile("member overlaps another ZIP structure")
    name = source.read(name_length)
    try:
        decoded = name.decode("utf-8" if flags & 0x800 else "cp437")
    except UnicodeDecodeError:
        raise zipfile.BadZipFile("invalid local filename") from None
    if decoded != info.orig_filename:
        raise zipfile.BadZipFile("local filename does not match ZIP directory")
    extra = source.read(extra_length)
    if len(extra) != extra_length:
        raise zipfile.BadZipFile("truncated local header")

    digest = hashlib.sha256()
    checksum = 0
    total = 0
    remaining = info.compress_size
    decoder = zlib.decompressobj(-15) if method == zipfile.ZIP_DEFLATED else None
    # zlib can consume the last input byte while still holding output.
    while remaining or (decoder and not decoder.eof):
        data = source.read(min(CHUNK, remaining))
        if remaining and not data:
            raise zipfile.BadZipFile("truncated ZIP member")
        remaining -= len(data)
        while True:
            if decoder:
                data_out = decoder.decompress(data, min(CHUNK, info.file_size - total + 1))
                if not data and not data_out and not decoder.eof:
                    raise zipfile.BadZipFile("incomplete deflate stream")
                data = decoder.unconsumed_tail
                if decoder.unused_data or (decoder.eof and remaining):
                    raise zipfile.BadZipFile("trailing compressed data")
            else:
                data_out, data = data, b""
            total += len(data_out)
            if total > info.file_size:
                raise zipfile.BadZipFile("uncompressed member exceeds declared size")
            checksum = zlib.crc32(data_out, checksum)
            digest.update(data_out)
            target.write(data_out)
            if not data:
                break
    if total != info.file_size or checksum != info.CRC:
        raise zipfile.BadZipFile("incorrect member size or CRC")
    if flags & 8:
        descriptor = source.read(min(16, end - source.tell()))
        values = (info.CRC, info.compress_size, info.file_size)
        plain = len(descriptor) >= 12 and struct.unpack_from("<3I", descriptor) == values
        signed = (len(descriptor) >= 16 and descriptor[:4] == b"PK\x07\x08"
                  and struct.unpack_from("<3I", descriptor, 4) == values)
        if not (plain or signed):
            raise zipfile.BadZipFile("invalid ZIP data descriptor")
    return {"size": total, "sha256": digest.hexdigest()}
