from app.database import SessionLocal
from app.models.db_models import Source


db = SessionLocal()

source = Source(
    source_type="pdf",
    source_name="test.pdf",
    source_identifier="pdf_001"
)

db.add(source)

db.commit()

print("Inserted Source ID:", source.id)

db.close()