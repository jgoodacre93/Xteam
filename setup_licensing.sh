#!/bin/bash
# ============================================
# Xteam Licensing System Setup Script
# ============================================
# This script generates the RSA key pair needed for the licensing system.
# Run this ONCE during initial setup.
#
# The private key stays on your server for generating licenses.
# The public key is embedded in license_validate.py for offline validation.
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRIVATE_KEY="$SCRIPT_DIR/server_private_key.pem"
PUBLIC_KEY="$SCRIPT_DIR/server_public_key.pem"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Xteam Licensing System Setup                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo "[ERROR] OpenSSL is not installed."
    echo "Install it with: sudo apt-get install openssl"
    exit 1
fi

# Check if keys already exist
if [ -f "$PRIVATE_KEY" ]; then
    echo "[WARNING] Private key already exists!"
    read -p "Overwrite? (y/N): " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

echo "[*] Generating RSA 2048-bit key pair..."
echo ""

# Generate private key
openssl genrsa -out "$PRIVATE_KEY" 2048 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to generate private key."
    exit 1
fi
echo "[✓] Private key generated: $PRIVATE_KEY"

# Extract public key
openssl rsa -in "$PRIVATE_KEY" -pubout -out "$PUBLIC_KEY" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to extract public key."
    exit 1
fi
echo "[✓] Public key generated: $PUBLIC_KEY"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                      IMPORTANT                              ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  1. Keep server_private_key.pem SECURE on your server        ║"
echo "║  2. Update license_validate.py with the public key           ║"
echo "║  3. Use generate_license.py to create licenses for users     ║"
echo "║  4. Never share the private key                              ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Display the public key for embedding
echo "Public key to embed in license_validate.py:"
echo "---"
cat "$PUBLIC_KEY"
echo "---"
echo ""

# Set proper permissions
chmod 600 "$PRIVATE_KEY"
chmod 644 "$PUBLIC_KEY"

echo "[*] Key permissions set (private: 600, public: 644)"
echo ""
echo "[✓] Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Update the public key in license_validate.py"
echo "  2. Set up your license validation API endpoint"
echo "  3. Configure the payment processing page"
