from datetime import datetime, timezone

from app.extensions import db


class Portfolio(db.Model):
    __tablename__ = "portfolios"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_name = db.Column(db.String(100), nullable=True)
    school_year = db.Column(db.Integer, nullable=True)
    semester = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    student = db.relationship("User", back_populates="portfolios")
    evidence_items = db.relationship(
        "PortfolioEvidence", back_populates="portfolio", cascade="all, delete-orphan"
    )
    submissions = db.relationship(
        "PortfolioSubmission", back_populates="portfolio", cascade="all, delete-orphan",
        order_by="PortfolioSubmission.version_no",
    )


class PortfolioEvidence(db.Model):
    __tablename__ = "portfolio_evidence"

    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(
        db.Integer, db.ForeignKey("portfolios.id"), nullable=False, index=True
    )
    evidence_type = db.Column(db.String(30), nullable=False)
    display_name = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    portfolio = db.relationship("Portfolio", back_populates="evidence_items")
