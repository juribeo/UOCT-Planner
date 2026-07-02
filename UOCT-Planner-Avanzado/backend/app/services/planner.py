from app.models.entities import Solicitud, Historial
INSPECTORES=['Jorge','Natalia']; HORARIOS=['10:00','12:00','14:00','16:00']
def generar_agenda_basica(db, fecha):
    for e in db.query(Solicitud).filter(Solicitud.fecha_agendada==fecha, Solicitud.estado=='Agendada').all():
        e.estado='Pendiente'; e.fecha_agendada=None; e.hora_agendada=None
    rows=db.query(Solicitud).filter(Solicitud.estado.in_(['Pendiente','Lista para agendar']), Solicitud.estado_documental.in_(['No revisada','Completa','No aplica'])).order_by(Solicitud.comuna, Solicitud.prioridad.desc(), Solicitud.tipo_actividad, Solicitud.created_at).limit(8).all()
    carga={i:0 for i in INSPECTORES}; out=[]
    for sol in rows:
        insp=sol.inspector_asignado if sol.inspector_asignado in INSPECTORES else min(carga, key=carga.get)
        if carga[insp]>=len(HORARIOS): continue
        sol.inspector_asignado=insp; sol.fecha_agendada=fecha; sol.hora_agendada=HORARIOS[carga[insp]]; sol.estado='Agendada'; carga[insp]+=1; out.append(sol)
        db.add(Historial(solicitud_id=sol.id,accion='Agenda generada',detalle=f'{fecha} {sol.hora_agendada} - {insp}',usuario='Sistema'))
    db.commit(); return out
