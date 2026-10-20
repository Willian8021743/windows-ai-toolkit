import importlib.util, os

_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pure_twofish.py")
_spec = importlib.util.spec_from_file_location("_pure_twofish", _p)
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)


class Twofish:
    def __init__(self, key):
        if isinstance(key, (bytes, bytearray)):
            self.key = bytes(key).hex()
        else:
            self.key = str(key)
        self.key = self.key.zfill(32)

    def encrypt(self, block):
        return bytes.fromhex(_m.encrypt(bytes(block).hex(), self.key))

    def decrypt(self, block):
        return bytes.fromhex(_m.decrypt(bytes(block).hex(), self.key))
