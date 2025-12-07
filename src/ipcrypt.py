import os
import argparse
import zlib
import base64
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

#!/usr/bin/env python3
"""
Proof-of-concept: compress a plaintext IP address and encrypt it with a local AES key (AES-GCM).
Saves/loads a local key file and prints a base64 URL-safe token suitable for use in a DNS TXT record.

Usage examples:
    Generate a key (writes aes_key.bin):
        python3 untitled_poc.py --generate-key

    Encrypt the example IP (123.123.123.123) and print token:
        python3 untitled_poc.py --encrypt

    Decrypt a token:
        python3 untitled_poc.py --decrypt <base64-token>

Dependencies:
    pip install cryptography
"""


DEFAULT_KEY_FILE = "aes_key.bin"
DEFAULT_IP = "123.123.123.123"
NONCE_SIZE = 12  # recommended for AESGCM (32-byte AES-256-GCM)


def generate_key(path: str, force: bool = False) -> bytes:
        p = Path(path)
        if p.exists() and not force:
                raise FileExistsError(f"Key file {path} already exists. Use --force to overwrite.")
        key = AESGCM.generate_key(bit_length=256)
        # write atomically
        tmp = p.with_suffix(".tmp")
        with open(tmp, "wb") as f:
                f.write(key)
        os.replace(tmp, p)
        os.chmod(p, 0o600)
        return key


def load_key(path: str) -> bytes:
        p = Path(path)
        if not p.exists():
                raise FileNotFoundError(f"Key file {path} not found. Generate one with --generate-key")
        return p.read_bytes()


def encrypt_text(key: bytes, plaintext: str) -> str:
        compressed = zlib.compress(plaintext.encode("utf-8"))
        aesgcm = AESGCM(key)
        nonce = os.urandom(NONCE_SIZE)
        ct = aesgcm.encrypt(nonce, compressed, None)
        token = base64.urlsafe_b64encode(nonce + ct).decode("ascii")
        return token


def decrypt_text(key: bytes, token: str) -> str:
        data = base64.urlsafe_b64decode(token.encode("ascii"))
        nonce = data[:NONCE_SIZE]
        ct = data[NONCE_SIZE:]
        aesgcm = AESGCM(key)
        decompressed = aesgcm.decrypt(nonce, ct, None)
        return zlib.decompress(decompressed).decode("utf-8")


def main():
        p = argparse.ArgumentParser(description="Compress + AES-GCM encrypt a short text (IP) for DNS TXT.")
        p.add_argument("--key-file", default=DEFAULT_KEY_FILE, help="Path to local AES key file")
        p.add_argument("--generate-key", action="store_true", help="Create a new AES-256 key file")
        p.add_argument("--force", action="store_true", help="Overwrite existing key when generating")
        p.add_argument("--encrypt", nargs="?", const=DEFAULT_IP, help="Encrypt provided text (default is example IP)")
        p.add_argument("--decrypt", help="Decrypt provided base64-token and print the plaintext")
        args = p.parse_args()

        try:
                if args.generate_key:
                        key = generate_key(args.key_file, force=args.force)
                        print(f"Key generated and saved to {args.key_file}")
                        return

                if args.encrypt is not None:
                        key = load_key(args.key_file)
                        token = encrypt_text(key, args.encrypt)
                        print(token)
                        return

                if args.decrypt:
                        key = load_key(args.key_file)
                        plain = decrypt_text(key, args.decrypt)
                        print(plain)
                        return

                p.print_help()
        except Exception as e:
                print("Error:", e)


if __name__ == "__main__":
        main()