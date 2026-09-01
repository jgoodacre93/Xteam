#!/usr/bin/env python3
import base64, hashlib, os, sys, json, platform, time

__ = lambda x: base64.b64decode(x).decode()
___ = lambda x: hashlib.sha256(x).hexdigest()

# Encoded string table
_S = {
    'a': 'aHR0cHM6Ly94bm93c2V2LmFpLnN0dWRpby9hcGkvdmFsaWRhdGUtbGljZW5zZQ==',
    'b': 'bGljZW5zZS5saWM=',
    'c': 'ZW1haWw=',
    'd': 'a2V5',
    'e': 'dmFsaWQ=',
    'f': 'c2lnbmF0dXJl',
    'g': 'cGF5',
    'aG9tZQ==': 'aG9tZQ==',
    'h': 'WC1UZWFtLUxpY2Vuc2Ut',
    'i': 'c3RhdHVz',
    'j': 'VHJhY2VyUGlk',
    'k': 'Z2V0dHJhY2U=',
    'bGludXg': 'bGludXg=',
    'bWFj': 'bWFj',
    'd2lu': 'd2lu',
}

def __getattr__(name):
    if name in _S:
        return __(_S[name])
    raise AttributeError(name)

def _anti_debug():
    """Multi-layer debugger detection"""
    _checks = []

    # Check 1: ptrace status on Linux
    if platform.system() == 'Linux':
        try:
            _status_path = f'/proc/{os.getpid()}/status'
            with open(_status_path) as _f:
                for _line in _f:
                    if 'TracerPid:' in _line:
                        _tracer = int(_line.split(':')[1].strip())
                        _checks.append(_tracer != 0)
        except:
            _checks.append(False)

    # Check 2: Python trace function
    if hasattr(sys, 'gettrace'):
        _checks.append(sys.gettrace() is not None)

    # Check 3: Timing analysis (debugger slows execution)
    _t1 = time.time()
    for _ in range(1000):
        pass
    _t2 = time.time()
    _checks.append((_t2 - _t1) > 0.1)

    # Check 4: Check for common debugger environment variables
    _debug_vars = ['GDB', 'STRACE', 'LTRACE', 'VALGRIND', 'LLDB']
    for _var in _debug_vars:
        if os.environ.get(_var):
            _checks.append(True)
            break

    return any(_checks)

def _self_integrity():
    """Verify script hasn't been modified"""
    try:
        _script = os.path.abspath(__file__)
        with open(_script, 'rb') as _f:
            _content = _f.read()
        _current = ___(_content)
        _hash_file = _script + '.hash'
        if os.path.exists(_hash_file):
            with open(_hash_file) as _f:
                _stored = _f.read().strip()
            return _current == _stored
        return True
    except:
        return True

def _self_destruct():
    """Remove all traces if tampering detected"""
    try:
        _script = os.path.abspath(__file__)
        _dir = os.path.dirname(_script)
        _targets = [
            _script,
            _script + '.hash',
            os.path.join(_dir, 'Xteam.sh'),
            os.path.join(_dir, 'license.lic'),
        ]
        for _t in _targets:
            if os.path.exists(_t):
                # Overwrite with random data before deletion
                with open(_t, 'wb') as _f:
                    _f.write(os.urandom(1024))
                os.remove(_t)
    except:
        pass
    os._exit(1)

def _generate_hash():
    """Generate integrity hash file"""
    try:
        _script = os.path.abspath(__file__)
        with open(_script, 'rb') as _f:
            _content = _f.read()
        _hash = ___(_content)
        with open(_script + '.hash', 'w') as _f:
            _f.write(_hash)
    except:
        pass

def _verify_signature(_email, _key, _sig):
    """Verify RSA signature offline"""
    _pub_key = __('LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUExSHcybkc4QVFSNkhtNndCZFcrdwpjM1VlbHo2U3J5d0JrU3R1S1VBblArM1Y0dWlWRVdtclM2Z2JicGNZbjFXQ1pkUll4eW1aWkxPQVdFclRXbkZ5Cm1RM0NmTmtiNTcydGk3MXZZR20rYXUrNlFETWJxTm51NVRMbzdhbFVHRVdvWUF1bXZDWVh0V3dydUFFRndVNnkKNURuaGVrbjNseWJ5UWtZR1Jhc3FjTFowZG9ScE5EWEprSTM2Nis5dzBid09FVGIwYUw1elY1TkVFS0d2TUZzeQplQ3h6aU0zZFVmNXYySTRQSmJ3dVZjNk82cTQyVHpmd1BNQnMxaGZ5VmIwZU1TZW1IcGVXV2ladmZhdzA2TFFZCnhEUnlGcTk4TlZ0NWNoTDB0V2ZTK3YrUzR6dFgvNGJQVmJDL003QmNuWmo1a3lVOFBUdEFwUnZqZC9YcGtYNXoKcVFJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0t')
    try:
        from Crypto.PublicKey import RSA
        from Crypto.Signature import pkcs1_15
        from Crypto.Hash import SHA256
        _pk = RSA.import_key(_pub_key)
        _msg = f'{_email}:{_key}'.encode()
        _h = SHA256.new(_msg)
        _sig_bytes = base64.b64decode(_sig)
        pkcs1_15.new(_pk).verify(_h, _sig_bytes)
        return True
    except ImportError:
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            _pk = serialization.load_pem_public_key(_pub_key.encode())
            _msg = f'{_email}:{_key}'.encode()
            _sig_bytes = base64.b64decode(_sig)
            _pk.verify(_sig_bytes, _msg, padding.PKCS1v15(), hashes.SHA256())
            return True
        except:
            return False
    except:
        return False

def _read_license():
    """Parse license file"""
    _lic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), __(_S['b']))
    if not os.path.exists(_lic_path):
        return None
    try:
        with open(_lic_path) as _f:
            _data = json.load(_f)
        return {
            'email': _data.get(__(_S['c']), ''),
            'key': _data.get(__(_S['d']), ''),
            'signature': _data.get(__(_S['f']), '')
        }
    except:
        return None

def _validate_online(_email, _key):
    """Server validation via HTTPS POST"""
    try:
        import urllib.request, ssl
        _payload = json.dumps({__(_S['c']): _email, __(_S['d']): _key}).encode()
        _ctx = ssl.create_default_context()
        _ctx.check_hostname = True
        _ctx.verify_mode = ssl.CERT_REQUIRED
        _req = urllib.request.Request(__(_S['a']), data=_payload,
                                      headers={'Content-Type': 'application/json',
                                               'User-Agent': 'Xteam-Validator/1.0'},
                                      method='POST')
        with urllib.request.urlopen(_req, timeout=10, context=_ctx) as _resp:
            _result = json.loads(_resp.read().decode())
            return _result.get(__(_S['e']), False)
    except:
        return None

def _validate_offline(_lic):
    """Offline signature validation"""
    if not _lic or not _lic.get('signature'):
        return False
    return _verify_signature(_lic['email'], _lic['key'], _lic['signature'])

def main():
    # Security checks
    if _anti_debug():
        _self_destruct()

    if not _self_integrity():
        _self_destruct()

    # Read license
    _license = _read_license()
    if not _license:
        sys.exit(1)

    # Online validation
    _online = _validate_online(_license['email'], _license['key'])
    if _online is True:
        sys.exit(0)
    elif _online is False:
        sys.exit(1)

    # Offline fallback
    if _validate_offline(_license):
        sys.exit(0)

    sys.exit(1)

if __name__ == '__main__':
    main()
