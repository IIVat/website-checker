from dotenv import load_dotenv

import os

# Load the environment variables from .env file
load_dotenv()

# Read the value of DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Example usage
if __name__ == "__main__":
    print(f"DATABASE_URL: {DATABASE_URL}")
