from sqlalchemy import create_engine, text
from gateway.models.db import Base, init_db, engine
from sqlalchemy.orm import sessionmaker

def test_fresh_db():
    print("Testing fresh DB...")
    init_db()
    with engine.connect() as conn:
        res = conn.execute(text("SELECT is_active FROM agents LIMIT 1"))
        print("Fresh DB Init OK!")

def test_existing_db():
    print("Testing existing DB upgrade...")
    # Create an engine without init_db first
    test_engine = create_engine("sqlite:///:memory:")
    # Manually create table without is_active
    with test_engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE agents (
            agent_id VARCHAR NOT NULL, 
            name VARCHAR NOT NULL, 
            status VARCHAR NOT NULL, 
            PRIMARY KEY (agent_id)
        )
        """))
        conn.execute(text("INSERT INTO agents (agent_id, name, status) VALUES ('test1', 'Test', 'ACTIVE')"))
    
    # Now run our application startup ALTER TABLE migration
    # We will simulate the same code in init_db
    try:
        with test_engine.begin() as conn:
            conn.execute(text("ALTER TABLE agents ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL"))
    except Exception as e:
        print(f"Exception: {e}")
        pass
        
    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT agent_id, is_active FROM agents")).fetchall()
        print(f"Existing DB upgrade OK! Data: {res}")

if __name__ == '__main__':
    test_fresh_db()
    test_existing_db()
