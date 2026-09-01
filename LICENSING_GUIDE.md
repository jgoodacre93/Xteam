# Xteam Licensing System - Integration Guide

## Overview

This licensing system provides secure, server-based license validation for the Xteam penetration testing tool. It includes:

- **Client-side validation** via obfuscated Python script
- **Online license verification** via HTTPS API
- **Offline fallback** using RSA cryptographic signatures
- **Anti-tampering protections** including self-destruct mechanisms
- **Payment integration** for premium feature unlocking

## File Structure

```
Xteam-main/
├── Xteam.sh                    # Main application (modified)
├── license_validate.py         # Obfuscated license validator
├── license_validate.py.hash    # Integrity hash for validator
├── generate_license.py         # Server-side license generator
├── setup_licensing.sh          # Initial setup script
├── license.lic                 # Customer license file (example)
└── server_private_key.pem      # Server private key (keep secure!)
```

## Quick Setup

### 1. Generate RSA Key Pair

Run the setup script to generate the cryptographic keys:

```bash
chmod +x setup_licensing.sh
./setup_licensing.sh
```

This creates:
- `server_private_key.pem` - Keep this SECURE on your server
- `server_public_key.pem` - Embedded in the client validator

### 2. Update Public Key in Validator

Edit `license_validate.py` and replace the public key with your generated one:

```python
_pub_key = """-----BEGIN PUBLIC KEY-----
YOUR_PUBLIC_KEY_HERE
-----END PUBLIC KEY-----"""
```

### 3. Regenerate Integrity Hash

After modifying the Python script, regenerate its hash:

```bash
sha256sum license_validate.py | awk '{print $1}' > license_validate.py.hash
```

### 4. Set Up License Server API

Create an endpoint at `https://xnowsev.ai.studio/api/validate-license` that:

- Accepts POST requests with JSON: `{"email": "...", "key": "..."}`
- Returns JSON: `{"valid": true}` or `{"valid": false}`

Example server implementation (Python Flask):

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_LICENSES = {
    "user@example.com": "XTEAM-ABCD-1234-EFGH"
}

@app.route('/api/validate-license', methods=['POST'])
def validate_license():
    data = request.get_json()
    email = data.get('email', '')
    key = data.get('key', '')

    is_valid = VALID_LICENSES.get(email) == key
    return jsonify({"valid": is_valid})

if __name__ == '__main__':
    app.run(ssl_context='adhoc')
```

### 5. Set Up Payment Page

Create a payment page at `https://xnowsev.ai.studio/pay` that:

- Accepts `email` and `session` query parameters
- Processes payment
- Generates a license key
- Calls `generate_license.py` to create a signed license
- Emails the license file to the customer

## Generating Licenses for Customers

After receiving payment, generate a license file:

```bash
python3 generate_license.py customer@email.com XTEAM-UNIQUE-KEY-HERE
```

This creates a `license.lic` file to send to the customer.

Example license file:

```json
{
  "email": "customer@email.com",
  "key": "XTEAM-UNIQUE-KEY-HERE",
  "signature": "base64_encoded_rsa_signature",
  "issued_at": "2024-01-15T10:30:00",
  "expires_at": "2025-01-15T10:30:00",
  "type": "premium"
}
```

## Feature Locking

### Free Features (Always Available)
1. Insta information gathering
2. OSINT - Email Harvesting
8. Update Xteam

### Premium Features (Require Valid License)
3. Crack android lockscreen interfaces
4. Phishing hacks
5. Web Vulnerability Scanner
6. Wireless Attacks
7. Android Virus link

10. Post-Exploitation
11. AI Assistant
12. Report Generator

## Security Features

### 1. Code Obfuscation
- Base64-encoded strings
- Runtime string decoding
- Minimal readable identifiers

### 2. Anti-Debugging
- ptrace detection (Linux)
- Python trace function detection
- Timing analysis
- Environment variable checks

### 3. Self-Integrity Verification
- SHA256 hash verification
- Automatic hash generation
- Tamper detection

### 4. Self-Destruct Mechanism
- Overwrites files with random data before deletion
- Removes validator, hash, and main script
- Triggered by tampering detection

### 5. Offline Validation
- RSA signature verification
- Works without internet connection
- Falls back when server unreachable

## API Reference

### License Validation Endpoint

**URL:** `POST https://xnowsev.ai.studio/api/validate-license`

**Request:**
```json
{
  "email": "user@example.com",
  "key": "XTEAM-ABCD-1234-EFGH"
}
```

**Response (valid):**
```json
{
  "valid": true
}
```

**Response (invalid):**
```json
{
  "valid": false
}
```

### Payment Initiation

**URL:** `GET https://xnowsev.ai.studio/pay?email=USER_EMAIL&session=UNIQUE_ID`

**Parameters:**
- `email` - Customer email for license delivery
- `session` - Unique payment session ID (UUID)

## Troubleshooting

### License Not Validating
1. Check that `license.lic` exists in the Xteam directory
2. Verify the license file contains valid JSON
3. Ensure the public key matches the private key used for signing
4. Check internet connection for online validation

### Python Script Errors
1. Ensure Python 3 is installed: `python3 --version`
2. Install required packages: `pip3 install pycryptodome`
3. Check file permissions: `chmod +x license_validate.py`

### Self-Destruct Triggered
1. Regenerate the integrity hash: `sha256sum license_validate.py > license_validate.py.hash`
2. Ensure no debugger is attached
3. Check for modified script content

## License

This licensing system is proprietary. Do not distribute the private key or validation logic.
