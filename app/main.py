from fastapi import FastAPI
from sqlalchemy import text

from app.routes.auth_routes import router as auth_router
from app.routes.profile_routes import router as profile_router
from app.routes.home_routes import router as home_router
from app.routes.document_routes import router as document_router
from app.routes.application_routes import router as application_router

from app.db.database import Base, engine
from app.models import user_model

app = FastAPI()

# create tables
Base.metadata.create_all(bind=engine)


# ==========================
# AUTO DB UPDATE (STARTUP)
# ==========================
@app.on_event("startup")
def update_database():

    with engine.connect() as conn:

        # BIO COLUMN
        result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name='users'
          AND column_name='bio'
        """))

        if not result.fetchone():
            conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN bio VARCHAR(255)
            """))
            conn.commit()

        # ROLE COLUMN
        result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name='users'
          AND column_name='role'
        """))

        if not result.fetchone():
            conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN role VARCHAR(50) DEFAULT 'user'
            """))
            conn.commit()

        # ALTERNATE PHONE
        result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name='users'
          AND column_name='alternate_phone'
        """))

        if not result.fetchone():
            conn.execute(text("""
            ALTER TABLE users
            ADD COLUMN alternate_phone VARCHAR(20)
            """))
            conn.commit()

        # OTP VERIFY
        result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name='otps'
          AND column_name='isVerify'
        """))

        if not result.fetchone():
            conn.execute(text("""
            ALTER TABLE otps
            ADD COLUMN isVerify BOOLEAN DEFAULT FALSE
            """))
            conn.commit()

        # DOCUMENT NUMBER
        result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name='documents'
          AND column_name='document_number'
        """))

        if not result.fetchone():
            conn.execute(text("""
            ALTER TABLE documents
            ADD COLUMN document_number VARCHAR(100)
            """))
            conn.commit()

        # APPLICATION CREATED_AT
        result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name='applications'
          AND column_name='created_at'
        """))

        if not result.fetchone():
            conn.execute(text("""
            ALTER TABLE applications
            ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()


# ==========================
# ROUTERS
# ==========================
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(document_router)
app.include_router(home_router)
app.include_router(application_router)


# ==========================
# ROOT
# ==========================
@app.get("/")
def root():
    return {"message": "Life Services API Running"}
