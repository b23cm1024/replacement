from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# In production (EC2), the deploy workflow passes a single DATABASE_URL secret.
# In local dev, you can either set DATABASE_URL directly in .env, or fall back
# to the individual DB_* vars for convenience.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Local dev fallback: build URL from individual vars
    DATABASE_URL = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()