#!/usr/bin/env python3
"""
License Generation Script for Xteam Server
This script generates signed license files for customers.
Run this on your server after receiving payment confirmation.

Domain: https://xnowsev.ai.studio/

Usage: python3 generate_license.py <customer_email> <license_key>
"""

import json
import base64
import sys
import os
from datetime import datetime, timedelta, timezone

# RSA Private Key for signing licenses
# IMPORTANT: Keep this key secure on your server only!
# Generate with: openssl genrsa -out private_key.pem 2048
PRIVATE_KEY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server_private_key.pem')

# Public key to embed in client validator (must match)
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1Hw2nG8AQR6Hm6wBdW+w
c3Uelz6SrywBkStuKUAnP+3V4uiVEWmrS6gbbpcYn1WCZdRYxymZZLOAWErTWnFy
mQ3CfNkb572ti71vYGm+au+6QDMbqNnu5TLo7alUGEWoYAumvCYXtWwruAEFwU6y
5Dnhekn3lybyQkYGRasqcLZ0doRpNDXJkI366+9w0bwOETb0aL5zV5NEEKGvMFsy
eCxziM3dUf5v2I4PJbwuVc6O6q42TzfwPMBs1hfyVb0eMSemHpeWWiZvfaw06LQY
xDRyFq98NVt5chL0tWfS+v+S4ztX/4bPVbC/M7BcnZj5kyU8PTtApRvjd/XpkX5z
qQIDAQAB
-----END PUBLIC KEY-----"""

def load_private_key():
    """Load RSA private key from file"""
    from Crypto.PublicKey import RSA
    if not os.path.exists(PRIVATE_KEY_PATH):
        print(f"[ERROR] Private key not found at {PRIVATE_KEY_PATH}")
        print("[INFO] Generate one with: openssl genrsa -out server_private_key.pem 2048")
        sys.exit(1)
    with open(PRIVATE_KEY_PATH) as f:
        return RSA.import_key(f.read())

def generate_license(email, license_key):
    """Generate a signed license file"""
    from Crypto.Signature import pkcs1_15
    from Crypto.Hash import SHA256

    private_key = load_private_key()

    # Create message to sign
    message = f"{email}:{license_key}".encode()
    h = SHA256.new(message)

    # Sign the message
    signature = pkcs1_15.new(private_key).sign(h)
    signature_b64 = base64.b64encode(signature).decode()

    # Create license data
    license_data = {
        "email": email,
        "key": license_key,
        "signature": signature_b64,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        "type": "premium"
    }

    return license_data

def main():
    if len(sys.argv) < 3:
        print("=" * 60)
        print("Xteam License Generator")
        print("=" * 60)
        print()
        print("Usage: python3 generate_license.py <customer_email> <license_key>")
        print()
        print("Example:")
        print("  python3 generate_license.py user@example.com XTEAM-ABCD-1234-EFGH")
        print()
        print("This will generate a license.lic file to send to the customer.")
        sys.exit(1)

    email = sys.argv[1]
    license_key = sys.argv[2]

    print("=" * 60)
    print("Generating License File")
    print("=" * 60)
    print(f"Email: {email}")
    print(f"Key: {license_key}")
    print()

    license_data = generate_license(email, license_key)

    # Save license file
    output_file = "license.lic"
    with open(output_file, 'w') as f:
        json.dump(license_data, f, indent=2)

    print(f"[✓] License file generated: {output_file}")
    print()
    print("License contents:")
    print(json.dumps(license_data, indent=2))
    print()
    print("[INFO] Send this file to the customer.")
    print("[INFO] They should place it in the Xteam installation directory.")

if __name__ == '__main__':
    main()
