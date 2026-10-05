import io,struct,zipfile,zlib
import numpy as np
import pytest
from aquavision.data.reference_ranges import parse_multipart,decode_zip_member,load_reference


def response(parts,total=100):
    result=b''
    for start,body in parts:
        result+=f'\n--BOUNDARY\nContent-Type: application/octet-stream\nContent-Range: bytes {start}-{start+len(body)-1}/{total}\n\n'.encode()+body
    return result+b'\n--BOUNDARY--\n'


def test_multipart_binary_and_order():
    raw=response([(30,b'\x00\n--BOUNDARY\n'),(0,b'abcd')])
    parts=parse_multipart(raw,[(0,3),(30,42)],100)
    assert parts[(0,3)]==b'abcd'
    assert parts[(30,42)]==b'\x00\n--BOUNDARY\n'


def test_reject_missing_duplicate_wrong_total_truncated():
    for raw,req in [(response([(0,b'ab')]),[(0,1),(5,6)]),
                    (response([(0,b'ab'),(0,b'ab')]),[(0,1)]),
                    (response([(0,b'ab')],101),[(0,1)]),
                    (response([(0,b'ab')])[:-5],[(0,1)])]:
        with pytest.raises(ValueError): parse_multipart(raw,req,100)


def test_zip_payload_crc_and_npy_alignment():
    data=io.BytesIO(); np.save(data,np.arange(4096,dtype=np.uint8).reshape(1,64,64)); raw=data.getvalue()
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('test_cyan.npy',raw)
    with zipfile.ZipFile(stream) as z:info=z.getinfo('test_cyan.npy')
    entry={'member':info.filename,'compression':info.compress_type,'size_bytes':info.file_size,'compressed_bytes':info.compress_size,'crc32':f'{info.CRC:08x}'}
    assert decode_zip_member(stream.getvalue(),entry)==raw
    assert load_reference(raw).shape==(1,64,64)
    with pytest.raises(ValueError):decode_zip_member(stream.getvalue(),{**entry,'crc32':'00000000'})
    with pytest.raises(ValueError):decode_zip_member(stream.getvalue(),{**entry,'member':'wrong'})
    bad=io.BytesIO();np.save(bad,np.zeros((64,64),dtype=np.uint8))
    with pytest.raises(ValueError):load_reference(bad.getvalue())


def test_coalescing_does_not_read_intervening_imagery():
    from aquavision.data.reference_ranges import coalesce_touching
    assert coalesce_touching([(8,9),(0,3),(4,6)])==[(0,6),(8,9)]
