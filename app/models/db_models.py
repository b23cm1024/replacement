from sqlalchemy import (
    Column,
    Integer,
    Text,
    JSON,
    ForeignKey
)

from pgvector.sqlalchemy import Vector

from app.database import Base


class Source(Base):

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)

    source_type = Column(Text)

    source_name = Column(Text)

    source_identifier = Column(Text)

class DocumentChunk(Base):

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True)

    source_id = Column(
        Integer,
        ForeignKey("sources.id")
    )

    chunk_title = Column(Text)

    chunk_text = Column(Text)

    chunk_index = Column(Integer)

    chunk_metadata = Column(JSON)

    embedding = Column(Vector(384))