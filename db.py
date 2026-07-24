from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "mysql+pymysql://3taZytz9rxBCMNf.root:s6GoZtbdZmHNePvG@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/ai_career_copilot"

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={
            "ssl": {
                "ssl": True
            }
        }
    )
    # Test connection
    with engine.connect() as conn:
        pass
    print("Database: Connected to TiDB Cloud.")
except Exception as e:
    print(f"Database: TiDB connection failed ({e}). Falling back to local SQLite.")
    DATABASE_URL = "sqlite:///ai_career_copilot.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()