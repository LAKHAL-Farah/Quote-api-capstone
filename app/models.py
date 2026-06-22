from sqlalchemy import Column,Integer,String,DateTime
from sqlalchemy.sql import func
from app.database import Base


class Quote(Base):
    __tablename__="quotes"

    id = Column(Integer,primary_key=True,index=True)
    text = Column(String,nullable=False)
    author = Column(String,nullable=False,index=True)
    category= Column(String,nullable=True,index=True)
    created_at = Column (DateTime(timezone=True),server_default=func.now())