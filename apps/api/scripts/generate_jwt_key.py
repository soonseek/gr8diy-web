"""Generate secure JWT secret key."""
import secrets


def main():
    """Generate and print a secure JWT secret key."""
    key = secrets.token_urlsafe(32)
    print("=" * 60)
    print("Generated JWT Secret Key:")
    print("=" * 60)
    print(key)
    print("=" * 60)
    print("\nAdd this to your .env file:")
    print(f"JWT_SECRET_KEY={key}")
    print("\nMake sure to keep this secret and never commit it to version control!")


if __name__ == "__main__":
    main()
