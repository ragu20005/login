import secrets

# Generate a secure random key
secret_key = secrets.token_hex(32)
print(f"Generated secret key: {secret_key}")