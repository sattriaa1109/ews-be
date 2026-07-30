from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), unique=True, nullable=False)
    source = Column(String(200))
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    raw_summary = Column(Text, nullable=True)

    alert = relationship("Alert", back_populates="article", uselist=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), unique=True)
    severity_score = Column(Float, default=0)
    matched_categories = Column(String(500))  # comma-separated
    matched_words = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    notified = Column(Integer, default=0)  # 0/1 sebagai boolean sqlite-friendly

    article = relationship("Article", back_populates="alert")
