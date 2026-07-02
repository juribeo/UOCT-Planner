import re, urllib.parse
ESTADOS=["Pendiente","Lista para agendar","Agendada","No agendable","Completada"]
DOCUMENTACION=["No revisada","Completa","Incompleta","No aplica"]
PRIORIDADES=["Normal","Alta","Urgente"]
INSPECTORES=["Jorge","Natalia"]
COMUNAS=["Maipú","Cerrillos","Quilicura","Huechuraba","Puente Alto","La Florida","Providencia","Las Condes","Santiago","Lampa","Colina","Buin","San Miguel","Ñuñoa","Macul","Pudahuel","Lo Prado","Conchalí","Recoleta","Estación Central","San Bernardo"]
def clean(v): return "" if v is None else str(v).strip()
def key(v): return re.sub(r"\s+"," ",clean(v)).upper()
def pick(row, aliases):
    low={key(k):v for k,v in row.items()}
    for a in aliases:
        if key(a) in low and clean(low[key(a)]): return clean(low[key(a)])
    for k,v in low.items():
        for a in aliases:
            if key(a) in k and clean(v): return clean(v)
    return ""
def maps_url(rows):
    pts=[]
    for r in rows:
        d=getattr(r,'direccion','') or '' ; c=getattr(r,'comuna','') or ''
        if d or c: pts.append(f"{d}, {c}, Región Metropolitana, Chile")
    return 'https://www.google.com/maps' if not pts else 'https://www.google.com/maps/dir/' + '/'.join(urllib.parse.quote_plus(p) for p in pts)
def classify_email_text(text):
    t=text.upper(); tipo='Solicitud'
    for k,v in {'RECEPCION':'Recepción','RECEPCIÓN':'Recepción','ENTREGA':'Entrega de Terreno','LIBRE TRANSITO':'Libre Tránsito','LIBRE TRÁNSITO':'Libre Tránsito','ENCENDIDO':'Encendido','MATERIALES':'Inspección de Materiales','AISLACION':'Prueba de Aislación','AISLACIÓN':'Prueba de Aislación','RECONFIGURACION':'Reconfiguración','RECONFIGURACIÓN':'Reconfiguración'}.items():
        if k in t: tipo=v; break
    comuna=''
    for c in COMUNAS:
        if key(c) in t: comuna=c; break
    return {'tipo_actividad':tipo,'comuna':comuna,'observaciones':text[:1500]}
