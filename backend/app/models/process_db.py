from datetime import datetime
import json
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base

class ProcessRecord(Base):
    __tablename__ = "processes"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_pages = Column(Integer, default=1)
    cnpj = Column(String, nullable=True, index=True)
    supplier_name = Column(String, nullable=True)
    total_pending = Column(Integer, default=0)
    overall_status = Column(String, default="PENDENTE")
    
    # Serialized JSON containing full ProcessAnalysisResponse
    analysis_json = Column(Text, nullable=False)

    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "created_at": self.created_at,
            "cnpj": self.cnpj,
            "supplier_name": self.supplier_name,
            "total_pending": self.total_pending,
            "overall_status": self.overall_status,
            "total_pages": self.total_pages,
        }

    def get_analysis_data(self) -> dict:
        return json.loads(self.analysis_json)
