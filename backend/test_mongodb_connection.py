import asyncio
import os
import sys
from dotenv import load_dotenv

# Reconfigure stdout/stderr encoding for Windows console compatibility
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Load environment variables
load_dotenv()


async def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    from motor.motor_asyncio import AsyncIOMotorClient

    mongodb_url = os.getenv(
        "MONGODB_URL",
        os.getenv("MONGODB_URI", "mongodb+srv://priyanshu1624:priyanshu1624a@cluster0.h5tji.mongodb.net/?appName=Cluster0")
    )

    print("\n" + "=" * 80)
    print("MONGODB CONNECTION TEST")
    print("=" * 80)
    print(f"Connection String (first 80 chars): {mongodb_url[:80]}...")
    print("=" * 80)

    try:
        # Create client
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        # Test connection
        print("\nAttempting to connect to MongoDB Atlas...")
        await client.admin.command("ping")
        print("✅ SUCCESS: MongoDB Atlas connection established!")
        print("✅ MongoDB is responding correctly to ping command")

        # Try serverInfo or db stats
        try:
            db = client.get_database("physioverse")
            stats = await db.command("dbStats")
            print(f"✅ Database Name: {db.name}")
            print(f"✅ Collection Count: {stats.get('collections', 0)}")
        except Exception:
            print("✅ Database handle initialized successfully")

        # Close connection
        client.close()
        print("✅ Connection closed successfully\n")
        return True

    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"❌ Error Message: {str(e)}")
        print("❌ Please verify:")
        print("   1. MongoDB Atlas cluster is active")
        print("   2. Username and password are correct")
        print("   3. Cluster name is correct (not <cluster>)")
        print("   4. IP whitelist includes your current IP")
        print("   5. Connection string has no special character issues\n")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_mongodb_connection())
    exit(0 if result else 1)
