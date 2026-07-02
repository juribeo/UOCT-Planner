from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database.connection import Base

class Solicitud(Base):
    __tablename__ = "solicitudes"
    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String, nullable=True)
    municipio = Column(String, nullable=True)
    proyecto = Column(String, nullable=True)
    comuna = Column(String, index=True, nullable=True)
    direccion = Column(String, nullable=True)
    tipo_actividad = Column(String, index=True, nullable=True)
    estado = Column(String, default="Pendiente", index=True)
    estado_documental = Column(String, default="No revisada", index=True)
    prioridad = Column(String, default="Normal", index=True)
    inspector_asignado = Column(String, nullable=True, index=True)
    fecha_solicitada = Column(String, nullable=True)
    fecha_agendada = Column(String, nullable=True, index=True)
    hora_agendada = Column(String, nullable=True)
    contacto = Column(String, nullable=True)
    correo_contacto = Column(String, nullable=True)
    origen = Column(String, nullable=True)
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Inspector(Base):
    __tablename__ = "inspectores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    correo = Column(String, nullable=True)
    activo = Column(String, default="SI")

class Historial(Base):
    __tablename__ = "historial"
    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, index=True)
    accion = Column(String, nullable=False)
    detalle = Column(Text, nullable=True)
    usuario = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
