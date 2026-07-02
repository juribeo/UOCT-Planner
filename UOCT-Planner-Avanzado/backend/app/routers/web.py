from fastapi import APIRouter,Request,Depends,UploadFile,File,Form
from fastapi.responses import RedirectResponse,StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import date,timedelta
import shutil,csv,io
from app.database.connection import get_db
from app.models.entities import Solicitud,Historial
from app.services.excel_importer import import_excel
from app.services.helpers import ESTADOS,DOCUMENTACION,PRIORIDADES,INSPECTORES,maps_url,classify_email_text
from app.services.planner import generar_agenda_basica
router=APIRouter(); BASE_DIR=Path(__file__).resolve().parents[1]; ROOT_DIR=BASE_DIR.parents[1]
templates=Jinja2Templates(directory=BASE_DIR/'templates'); UPLOADS=ROOT_DIR/'backend'/'uploads'; UPLOADS.mkdir(parents=True,exist_ok=True)
def ctx(request,**kw):
    d={'request':request,'estados':ESTADOS,'documentacion_opts':DOCUMENTACION,'prioridades':PRIORIDADES,'inspectores':INSPECTORES}; d.update(kw); return d
@router.get('/')
def dashboard(request:Request, db:Session=Depends(get_db)):
    total=db.query(Solicitud).count(); pendientes=db.query(Solicitud).filter(Solicitud.estado=='Pendiente').count(); listas=db.query(Solicitud).filter(Solicitud.estado=='Lista para agendar').count(); no_ag=db.query(Solicitud).filter(Solicitud.estado=='No agendable').count(); ag=db.query(Solicitud).filter(Solicitud.estado=='Agendada').count()
    proximas=db.query(Solicitud).filter(Solicitud.estado=='Agendada').order_by(Solicitud.fecha_agendada,Solicitud.hora_agendada).limit(12).all()
    conteo={}
    for (c,) in db.query(Solicitud.comuna).all(): conteo.__setitem__(c or 'Sin comuna', conteo.get(c or 'Sin comuna',0)+1)
    return templates.TemplateResponse('dashboard.html',ctx(request,total=total,pendientes=pendientes,listas=listas,no_agendables=no_ag,agendadas=ag,proximas=proximas,top_comunas=sorted(conteo.items(),key=lambda x:x[1],reverse=True)[:10]))
@router.get('/solicitudes')
def solicitudes(request:Request,q:str='',comuna:str='',estado:str='',inspector:str='',db:Session=Depends(get_db)):
    query=db.query(Solicitud)
    if q:
        like=f'%{q}%'; query=query.filter(Solicitud.empresa.like(like)|Solicitud.proyecto.like(like)|Solicitud.direccion.like(like)|Solicitud.tipo_actividad.like(like)|Solicitud.observaciones.like(like))
    if comuna: query=query.filter(Solicitud.comuna.like(f'%{comuna}%'))
    if estado: query=query.filter(Solicitud.estado==estado)
    if inspector: query=query.filter(Solicitud.inspector_asignado==inspector)
    return templates.TemplateResponse('solicitudes.html',ctx(request,rows=query.order_by(Solicitud.created_at.desc()).all(),q=q,comuna=comuna,estado=estado,inspector=inspector))
@router.get('/solicitudes/nueva')
def nueva(request:Request): return templates.TemplateResponse('editar_solicitud.html',ctx(request,r=None,historial=[],modo='Nueva'))
@router.get('/solicitud/{sid}')
def editar(request:Request,sid:int,db:Session=Depends(get_db)):
    return templates.TemplateResponse('editar_solicitud.html',ctx(request,r=db.query(Solicitud).filter(Solicitud.id==sid).first(),historial=db.query(Historial).filter(Historial.solicitud_id==sid).order_by(Historial.created_at.desc()).all(),modo='Editar'))
@router.post('/guardar-solicitud')
def guardar_solicitud(id:str=Form(''),empresa:str=Form(''),proyecto:str=Form(''),municipio:str=Form(''),comuna:str=Form(''),direccion:str=Form(''),tipo_actividad:str=Form(''),estado:str=Form('Pendiente'),estado_documental:str=Form('No revisada'),prioridad:str=Form('Normal'),inspector_asignado:str=Form(''),fecha_solicitada:str=Form(''),fecha_agendada:str=Form(''),hora_agendada:str=Form(''),contacto:str=Form(''),correo_contacto:str=Form(''),observaciones:str=Form(''),db:Session=Depends(get_db)):
    sol=db.query(Solicitud).filter(Solicitud.id==int(id)).first() if id else Solicitud(origen='Manual'); accion='Actualización' if id else 'Creación manual'
    if not id: db.add(sol); db.flush()
    for k,v in locals().items():
        if k in ['empresa','proyecto','municipio','comuna','direccion','tipo_actividad','estado','estado_documental','prioridad','inspector_asignado','fecha_solicitada','fecha_agendada','hora_agendada','contacto','correo_contacto','observaciones']: setattr(sol,k,v)
    db.add(Historial(solicitud_id=sol.id,accion=accion,detalle='Solicitud guardada',usuario='Jorge')); db.commit(); return RedirectResponse('/solicitudes',status_code=303)
@router.get('/importar')
def importar(request:Request): return templates.TemplateResponse('importar.html',ctx(request))
@router.post('/importar-excel')
async def importar_excel(file:UploadFile=File(...),db:Session=Depends(get_db)):
    path=UPLOADS/file.filename
    with path.open('wb') as b: shutil.copyfileobj(file.file,b)
    import_excel(path,db); return RedirectResponse('/solicitudes',status_code=303)
@router.post('/importar-correo')
async def importar_correo(file:UploadFile=File(...),db:Session=Depends(get_db)):
    text=(await file.read()).decode('utf-8',errors='ignore'); data=classify_email_text(text); sol=Solicitud(proyecto=file.filename,comuna=data['comuna'],tipo_actividad=data['tipo_actividad'],observaciones=data['observaciones'],origen='Correo manual')
    db.add(sol); db.flush(); db.add(Historial(solicitud_id=sol.id,accion='Importación correo',detalle=file.filename,usuario='Sistema')); db.commit(); return RedirectResponse('/solicitudes',status_code=303)
@router.get('/agenda')
def agenda(request:Request,db:Session=Depends(get_db)):
    rows=db.query(Solicitud).filter(Solicitud.estado=='Agendada').order_by(Solicitud.fecha_agendada,Solicitud.inspector_asignado,Solicitud.hora_agendada).all(); j=[r for r in rows if r.inspector_asignado=='Jorge']; n=[r for r in rows if r.inspector_asignado=='Natalia']
    return templates.TemplateResponse('agenda.html',ctx(request,rows=rows,jorge=j,natalia=n,maps_jorge=maps_url(j),maps_natalia=maps_url(n)))
@router.post('/generar-agenda')
def generar_agenda(fecha:str=Form(''),db:Session=Depends(get_db)):
    generar_agenda_basica(db, fecha or (date.today()+timedelta(days=1)).isoformat()); return RedirectResponse('/agenda',status_code=303)
@router.get('/agenda-semanal')
def agenda_semanal(request:Request,db:Session=Depends(get_db)):
    return templates.TemplateResponse('agenda_semanal.html',ctx(request,rows=db.query(Solicitud).filter(Solicitud.estado=='Agendada').order_by(Solicitud.fecha_agendada,Solicitud.inspector_asignado,Solicitud.hora_agendada).all()))
@router.get('/reportes')
def reportes(request:Request,db:Session=Depends(get_db)):
    rows=db.query(Solicitud).all(); pe={}; pt={}; pi={}
    for r in rows:
        pe[r.estado or 'Sin estado']=pe.get(r.estado or 'Sin estado',0)+1; pt[r.tipo_actividad or 'Sin tipo']=pt.get(r.tipo_actividad or 'Sin tipo',0)+1; pi[r.inspector_asignado or 'Sin asignar']=pi.get(r.inspector_asignado or 'Sin asignar',0)+1
    return templates.TemplateResponse('reportes.html',ctx(request,por_estado=pe,por_tipo=pt,por_inspector=pi))
@router.get('/exportar-solicitudes')
def exportar(db:Session=Depends(get_db)):
    rows=db.query(Solicitud).order_by(Solicitud.created_at.desc()).all(); out=io.StringIO(); wr=csv.writer(out,delimiter=';'); headers=['id','empresa','proyecto','municipio','comuna','direccion','tipo_actividad','estado','estado_documental','prioridad','inspector_asignado','fecha_solicitada','fecha_agendada','hora_agendada','origen','observaciones']; wr.writerow(headers)
    for r in rows: wr.writerow([getattr(r,h,'') or '' for h in headers])
    out.seek(0); return StreamingResponse(iter([out.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=solicitudes_uoct_planner.csv'})
@router.post('/limpiar')
def limpiar(db:Session=Depends(get_db)):
    db.query(Historial).delete(); db.query(Solicitud).delete(); db.commit(); return RedirectResponse('/',status_code=303)
