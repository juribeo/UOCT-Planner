from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.database.connection import Base, engine, SessionLocal
from app.models.entities import Inspector
from app.routers import web
BASE_DIR=Path(__file__).resolve().parent
app=FastAPI(title='UOCT Planner', version='0.5.0')
app.mount('/static', StaticFiles(directory=BASE_DIR/'static'), name='static')
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    for nombre,correo in [('Jorge','juribeo@mtt.gob.cl'),('Natalia','')]:
        if not db.query(Inspector).filter(Inspector.nombre==nombre).first(): db.add(Inspector(nombre=nombre,correo=correo,activo='SI'))
    db.commit()
finally: db.close()
app.include_router(web.router)
@app.get('/api/health')
def health(): return {'estado':'ok','version':'0.5.0'}
