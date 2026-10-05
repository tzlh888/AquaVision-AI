"""Strict multipart ZIP-member reads for reference-only census (Phase 3.5).

No full-response fallback, no pickle loading, no filesystem extraction of names.
Content counts are verified per member; CRC matches alone never infer labels.
"""
import io
import re
import struct
import zlib
import numpy as np


def coalesce_touching(ranges):
    """Merge only touching/overlapping requested bytes; never bridge imagery gaps."""
    result=[]
    for a,b in sorted(ranges):
        if a<0 or b<a:raise ValueError('Invalid range')
        if result and a<=result[-1][1]+1:
            result[-1]=(result[-1][0],max(b,result[-1][1]))
        else:result.append((a,b))
    return result


def parse_multipart(body, requested, archive_size):
    expected={(start,end) for start,end in requested}
    if len(expected)!=len(requested): raise ValueError('Duplicate requested ranges')
    first=re.match(br'\r?\n?--([A-Za-z0-9_-]{1,70})\r?\n',body)
    if not first: raise ValueError('Missing multipart boundary')
    boundary=first.group(1); pos=0; result={}
    pattern=re.compile(br'\r?\n?--'+re.escape(boundary)+br'(--)?\r?\n')
    while pos<len(body):
        match=pattern.match(body,pos)
        if not match: raise ValueError('Bad multipart framing')
        pos=match.end()
        if match.group(1):
            if body[pos:].strip(): raise ValueError('Trailing response bytes')
            break
        end_headers=re.search(br'\r?\n\r?\n',body[pos:])
        if not end_headers: raise ValueError('Missing part headers')
        headers=body[pos:pos+end_headers.start()]
        m=re.search(br'(?im)^Content-Range:\s*bytes (\d+)-(\d+)/(\d+)\s*$',headers)
        if not m: raise ValueError('Missing exact part Content-Range')
        a,b,total=map(int,m.groups()); key=(a,b)
        if total!=archive_size or key not in expected or key in result: raise ValueError('Unexpected/duplicate range')
        pos+=end_headers.end(); size=b-a+1
        result[key]=body[pos:pos+size]
        if len(result[key])!=size: raise ValueError('Truncated range')
        pos+=size
    else:
        raise ValueError('Missing closing boundary')
    if set(result)!=expected: raise ValueError('Missing requested range')
    return result


def decode_zip_member(payload,entry):
    if len(payload)<30: raise ValueError('Truncated local header')
    values=struct.unpack('<4s5H3I2H',payload[:30])
    signature,_,flags,method,_,_,_,_,_,n_name,n_extra=values
    if signature!=b'PK\x03\x04' or flags&1: raise ValueError('Invalid/encrypted ZIP member')
    if method!=int(entry['compression']) or method not in (0,8): raise ValueError('Unexpected compression')
    name=payload[30:30+n_name].decode('utf-8' if flags&0x800 else 'cp437')
    if name!=entry['member']: raise ValueError('Member identity mismatch')
    offset=30+n_name+n_extra; size=int(entry['compressed_bytes'])
    if size>2_000_000 or int(entry['size_bytes'])>2_000_000: raise ValueError('Member exceeds limit')
    compressed=payload[offset:offset+size]
    if len(compressed)!=size: raise ValueError('Truncated member')
    if method==0: raw=compressed
    else:
        decoder=zlib.decompressobj(-15)
        raw=decoder.decompress(compressed,int(entry['size_bytes'])+1)
        if not decoder.eof or decoder.unconsumed_tail or decoder.unused_data: raise ValueError('Invalid compressed stream')
    if len(raw)!=int(entry['size_bytes']) or zlib.crc32(raw)!=int(entry['crc32'],16): raise ValueError('CRC/size mismatch')
    return raw


def load_reference(raw):
    array=np.load(io.BytesIO(raw),allow_pickle=False)
    if array.shape!=(1,64,64) or array.dtype!=np.uint8: raise ValueError('Unexpected reference shape/dtype')
    return array
