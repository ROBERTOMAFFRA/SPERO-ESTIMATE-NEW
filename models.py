import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

# Pega o link do banco do Render automaticamente
DATABASE_URL = os.environ.get('DATABASE_URL')

# Corrige prefixo para compatibilidade com SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Conexão com o banco de dados PostgreSQL
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Model de Usuários
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    role = Column(String(50), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)

# Model de Estimativas
class Estimate(Base):
    __tablename__ = 'estimates'
    id = Column(Integer, primary_key=True, index=True)
    client = Column(String(100))
    description = Column(String(255))
    unit = Column(String(50))
    qty = Column(Float)
    price = Column(Float)
    total = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

# Inicializa/cria tabelas no banco
def init_db():
    Base.metadata.create_all(bind=engine)

