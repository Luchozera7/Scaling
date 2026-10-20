"""Arma los flujos de n8n de Scaling (archivos .json para importar) y la planilla modelo.

Las instrucciones de cada agente se leen de agentes/*.md, así que si se cambia un
agente alcanza con volver a correr esto y reimportar el flujo.

Uso:  python3 n8n/armar_flujos.py
"""

import json
import uuid
from pathlib import Path

from openpyxl import Workbook

RAIZ = Path(__file__).resolve().parent.parent
AGENTES = RAIZ / "agentes"
SALIDA = Path(__file__).resolve().parent
MODELO = "claude-opus-5-5"
PLANILLA = "PEGÁ ACÁ EL LINK DE TU PLANILLA"

# Pestañas de la planilla y sus columnas.
PESTANAS = {
    "Comercios": ["nombre", "rubro", "direccion", "localidad", "telefono", "web", "instagram",
                  "zona_cercana", "distancia_km", "fuente"],
    "Evaluaciones": ["fecha", "comercio", "total", "it_puntaje", "it_oferta", "it_motivo",
                     "prospeccion_puntaje", "prospeccion_motivo", "finanzas_puntaje",
                     "finanzas_motivo", "abono_mensual_ars", "detalle"],
    "Propuestas": ["fecha", "elegidos", "propuesta_para_el_ceo", "detalle"],
    "Adelantos": ["fecha", "comercio", "oferta", "que_va_a_ver_el_cliente", "legal", "supuestos", "html",
                  "revision_legal"],
    "Contratos": ["fecha", "comercio", "contrato_borrador", "falta_completar", "riesgos", "me_excede"],
    "Informes": ["fecha", "agente", "resumen", "detalle"],
    "Clientes": ["nombre", "rubro", "zona", "oferta", "abono_mensual_ars", "instagram", "notas"],
    "Caja": ["fecha", "concepto", "tipo", "monto", "cliente", "comprobante"],
    "Soporte": ["fecha", "sesion", "mensaje", "respuesta", "resuelto", "derivar_a_lucho",
                "resumen_para_lucho"],
    "FAQ": ["pregunta", "respuesta"],
    "Leads": ["fecha", "sesion", "mensaje", "respuesta", "lead_completo", "pide_persona", "nombre",
              "comercio", "rubro", "zona", "necesita", "horario_contacto"],
    "Info": ["texto"],
    "Seguimiento": ["comercio", "fecha_contacto", "respondio", "cerro", "motivo", "notas"],
}

INFO_SCALING = (
    "Scaling es una agencia de Tres de Febrero (Buenos Aires) que les arma herramientas digitales "
    "a comercios de barrio: turnos online, página web, chatbot de WhatsApp o Instagram, e "
    "inventario y caja. El dueño, Lucho, conoce cada comercio y arma un presupuesto a medida."
)

# Lee la respuesta de Claude y la convierte en datos. Se repite en cada nodo de código.
LEER = """function leer(r) {
  const texto = (r.merged_response ?? (r.content || []).filter(c => c.type === 'text').map(c => c.text).join(''))
    .trim().replace(/^```(json)?\\s*/, '').replace(/\\s*```$/, '');
  try { return JSON.parse(texto); } catch (e) { return { error: 'No se pudo leer la respuesta de Claude', texto }; }
}
const hoy = new Date().toISOString().slice(0, 10);
// Google Sheets acepta hasta 50.000 caracteres por celda.
const celda = s => (s && s.length > 45000 ? s.slice(0, 45000) + ' [cortado]' : s);
"""


def instrucciones(nombre):
    return (AGENTES / f"{nombre}.md").read_text(encoding="utf-8").strip()


class Flujo:
    def __init__(self, nombre, nota):
        self.nombre = nombre
        self.nodos = []
        self.conexiones = {}
        self.x = 0
        self.y = 0
        self.nota(nota, (-420, -260))

    def nodo(self, nombre, tipo, version, parametros, pos=None, **extra):
        if pos is None:
            pos = (self.x, 0)
            self.x += 240
        n = {"parameters": parametros, "id": str(uuid.uuid4()), "name": nombre, "type": tipo,
             "typeVersion": version, "position": list(pos), **extra}
        self.nodos.append(n)
        return nombre

    def nota(self, texto, pos, ancho=400, alto=240):
        self.nodo(f"Nota {len(self.nodos) + 1}", "n8n-nodes-base.stickyNote", 1,
                  {"content": texto, "width": ancho, "height": alto}, pos)

    def unir(self, desde, hasta, salida=0):
        lista = self.conexiones.setdefault(desde, {"main": []})["main"]
        while len(lista) <= salida:
            lista.append([])
        lista[salida].append({"node": hasta, "type": "main", "index": 0})

    def cadena(self, *nombres):
        for a, b in zip(nombres, nombres[1:]):
            self.unir(a, b)

    def guardar(self, archivo):
        datos = {"name": self.nombre, "nodes": self.nodos, "connections": self.conexiones,
                 "settings": {"executionOrder": "v1"}, "pinData": {}}
        (SALIDA / archivo).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


# --- Nodos que se repiten ---

def config(f, extra=None, pos=None):
    valores = [("planilla", PLANILLA, "string")] + (extra or [])
    return f.nodo("Config", "n8n-nodes-base.set", 3.4, {
        "mode": "manual",
        "assignments": {"assignments": [
            {"id": str(uuid.uuid4()), "name": n, "value": v, "type": t} for n, v, t in valores]},
        "options": {},
    }, pos)


def hoja(pestana):
    return {
        "documentId": {"__rl": True, "mode": "url", "value": "={{ $('Config').first().json.planilla }}"},
        "sheetName": {"__rl": True, "mode": "name", "value": pestana},
    }


def leer_hoja(f, nombre, pestana, pos=None):
    return f.nodo(nombre, "n8n-nodes-base.googleSheets", 4.7,
                  {"resource": "sheet", "operation": "read", **hoja(pestana), "options": {}},
                  pos, alwaysOutputData=True, executeOnce=False)


def guardar_hoja(f, nombre, pestana, pos=None):
    return f.nodo(nombre, "n8n-nodes-base.googleSheets", 4.7, {
        "resource": "sheet", "operation": "append", **hoja(pestana),
        "columns": {"mappingMode": "autoMapInputData", "value": {}, "matchingColumns": [], "schema": []},
        "options": {"handlingExtraData": "ignoreIt"},
    }, pos)


def claude(f, nombre, agente, mensaje, max_tokens=4000, pos=None, system=None):
    return f.nodo(nombre, "@n8n/n8n-nodes-langchain.anthropic", 1, {
        "resource": "text", "operation": "message",
        "modelId": {"__rl": True, "mode": "id", "value": MODELO},
        "messages": {"values": [{"content": mensaje, "role": "user"}]},
        "simplify": True,
        "options": {"system": system or instrucciones(agente), "includeMergedResponse": True,
                    "maxTokens": max_tokens},
    }, pos)


def codigo(f, nombre, js, por_item=False, pos=None):
    p = {"jsCode": LEER + js}
    if por_item:
        p["mode"] = "runOnceForEachItem"
    return f.nodo(nombre, "n8n-nodes-base.code", 2, p, pos)


def disparadores(f, regla):
    a = f.nodo("Probar a mano", "n8n-nodes-base.manualTrigger", 1, {}, (f.x, -120))
    b = f.nodo("Automático", "n8n-nodes-base.scheduleTrigger", 1.2,
               {"rule": {"interval": [regla]}}, (f.x, 120))
    f.x += 240
    return a, b


# --- 1. Mesa chica semanal ---

def mesa_chica():
    f = Flujo("Scaling 1 - Mesa chica semanal", (
        "## Mesa chica semanal\n"
        "1. En **Config** pegá el link de tu planilla y el valor de tu hora.\n"
        "2. En cada nodo de Claude y de Google Sheets elegí tu credencial.\n"
        "3. Para probar: **Execute workflow**. Evalúa los primeros comercios (max_comercios en Config).\n"
        "4. El resultado queda en las pestañas **Evaluaciones**, **Adelantos** y **Propuestas**.\n\n"
        "El disparador Automático corre los lunes a las 9 cuando publiques el flujo."))
    a, b = disparadores(f, {"field": "weeks", "triggerAtDay": [1], "triggerAtHour": 9})
    c = config(f, [("max_comercios", 5, "number"), ("valor_hora_ars", "sin definir", "string")])
    f.unir(a, c)
    f.unir(b, c)
    leer = leer_hoja(f, "Leer comercios", "Comercios")
    lim = f.nodo("Limitar comercios", "n8n-nodes-base.limit", 1,
                 {"maxItems": "={{ $('Config').first().json.max_comercios }}"})
    it = claude(f, "IT y Producto", "it_producto", "=Comercio:\n{{ JSON.stringify($json) }}")
    l_it = codigo(f, "Leer IT", "return { comercio: $('Limitar comercios').item.json, it: leer($json) };",
                  por_item=True)
    pr = claude(f, "Prospección", "prospeccion",
                "={{ JSON.stringify({ comercio: $json.comercio, it_y_producto: $json.it }) }}")
    l_pr = codigo(f, "Leer Prospección",
                  "return { ...$('Leer IT').item.json, prospeccion: leer($json) };", por_item=True)
    fi = claude(f, "Finanzas", "finanzas", (
        "=Valor de la hora de trabajo (definido por el CEO): {{ $('Config').first().json.valor_hora_ars }}\n"
        "Resumen del Contador: todavía no hay.\n\n"
        "{{ JSON.stringify({ comercio: $json.comercio, it_y_producto: $json.it, prospeccion: $json.prospeccion }) }}"),
        max_tokens=6000)
    l_fi = codigo(f, "Leer Finanzas", (
        "const e = { ...$('Leer Prospección').item.json, finanzas: leer($json) };\n"
        "e.total = (Number(e.it.puntaje) || 0) + (Number(e.prospeccion.puntaje) || 0) + (Number(e.finanzas.puntaje) || 0);\n"
        "return e;"), por_item=True)
    fila = codigo(f, "Armar fila", (
        "return {\n"
        "  fecha: hoy, comercio: $json.comercio.nombre, total: $json.total,\n"
        "  it_puntaje: $json.it.puntaje, it_oferta: $json.it.oferta, it_motivo: $json.it.motivo,\n"
        "  prospeccion_puntaje: $json.prospeccion.puntaje, prospeccion_motivo: $json.prospeccion.motivo,\n"
        "  finanzas_puntaje: $json.finanzas.puntaje, finanzas_motivo: $json.finanzas.motivo,\n"
        "  abono_mensual_ars: $json.finanzas.presupuesto?.abono_mensual_ars,\n"
        "  detalle: celda(JSON.stringify({ it: $json.it, prospeccion: $json.prospeccion, finanzas: $json.finanzas })),\n"
        "};"), por_item=True)
    g_ev = guardar_hoja(f, "Guardar evaluaciones", "Evaluaciones")
    top = codigo(f, "Elegir los 5 mejores", (
        "return $('Leer Finanzas').all().map(i => i.json)\n"
        "  .sort((a, b) => b.total - a.total).slice(0, 5).map(json => ({ json }));"))
    ad = claude(f, "Adelanto", "adelanto", (
        "={{ JSON.stringify({ comercio: $json.comercio, oferta: $json.it }) }}"), max_tokens=8000)
    l_ad = codigo(f, "Leer adelanto", "return { ...$('Elegir los 5 mejores').item.json, adelanto: leer($json) };",
                  por_item=True)
    le = claude(f, "Legal", "legal", (
        "={{ JSON.stringify({ comercio: $json.comercio, oferta: $json.it, presupuesto: $json.finanzas, adelanto: $json.adelanto }) }}"))
    l_le = codigo(f, "Juntar para el Jefe", (
        "const legal = $input.all().map(i => leer(i.json));\n"
        "// Al Jefe le alcanza con saber qué muestra cada adelanto, sin la página entera.\n"
        "const adelantos = $('Leer adelanto').all().map(i => { const { html, ...resto } = i.json.adelanto; return resto; });\n"
        "const evaluaciones = $('Leer Finanzas').all().map(i => i.json);\n"
        "return [{ json: { evaluaciones, adelantos, legal } }];"))
    je = claude(f, "Jefe de Gabinete", "jefe_de_gabinete", "={{ JSON.stringify($json) }}", max_tokens=12000)
    l_je = codigo(f, "Armar propuesta", (
        "const j = leer($json);\n"
        "return [{ json: {\n"
        "  fecha: hoy,\n"
        "  elegidos: (j.elegidos || []).map(e => e.comercio).join(', '),\n"
        "  propuesta_para_el_ceo: j.propuesta_para_el_ceo || j.texto,\n"
        "  detalle: celda(JSON.stringify(j)),\n"
        "} }];"))
    g_pr = guardar_hoja(f, "Guardar propuesta", "Propuestas")
    f.cadena(c, leer, lim, it, l_it, pr, l_pr, fi, l_fi, fila, g_ev, top, ad, l_ad, le, l_le, je, l_je, g_pr)
    # Cada adelanto va a su propia fila en "Adelantos", con lo que dijo Legal.
    x_legal = next(n["position"][0] for n in f.nodos if n["name"] == le)
    fa = codigo(f, "Armar adelanto", (
        "const r = leer($json);\n"
        "const e = $('Leer adelanto').item.json;\n"
        "return { fecha: hoy, comercio: e.comercio.nombre, oferta: e.it.oferta,\n"
        "  que_va_a_ver_el_cliente: e.adelanto.que_va_a_ver_el_cliente || e.adelanto.error,\n"
        "  legal: [r.se_puede_ofrecer, r.motivo || r.texto].filter(Boolean).join('. '),\n"
        "  supuestos: celda(JSON.stringify(e.adelanto.supuestos || [])), html: celda(e.adelanto.html || ''),\n"
        "  revision_legal: celda(JSON.stringify(r)) };"), por_item=True, pos=(x_legal + 240, 240))
    g_ad = guardar_hoja(f, "Guardar adelantos", "Adelantos", (x_legal + 480, 240))
    f.cadena(le, fa, g_ad)
    # Ejecutar "Elegir los 5 mejores" una sola vez aunque se guarden varias filas.
    for n in f.nodos:
        if n["name"] == "Elegir los 5 mejores":
            n["executeOnce"] = True
    f.guardar("1_mesa_chica_semanal.json")


# --- 2. Informes del mes ---

def informes():
    f = Flujo("Scaling 2 - Informes del mes", (
        "## Informes del mes\n"
        "Contador, Posventa y Marketing. Cada uno lee su pestaña y deja su informe en **Informes**.\n"
        "1. En **Config** pegá el link de tu planilla.\n"
        "2. Elegí tus credenciales en cada nodo.\n"
        "3. Para probar: **Execute workflow**.\n\n"
        "El disparador Automático corre el día 1 de cada mes a las 9."))
    a, b = disparadores(f, {"field": "months", "triggerAtDayOfMonth": 1, "triggerAtHour": 9})
    c = config(f)
    f.unir(a, c)
    f.unir(b, c)
    x0 = f.x

    def informe(nombre_agente, resumen):
        return codigo(f, f"Informe {nombre_agente}", (
            "const r = leer($json);\n"
            f"return [{{ json: {{ fecha: hoy, agente: '{nombre_agente}', resumen: {resumen}, detalle: celda(JSON.stringify(r)) }} }}];"),
            pos=(f.x, f.y))

    # Contador
    f.y = -300
    f.x = x0
    caja = leer_hoja(f, "Leer caja", "Caja", (f.x, f.y)); f.x += 240
    cli1 = leer_hoja(f, "Leer clientes (Contador)", "Clientes", (f.x, f.y)); f.x += 240
    j1 = codigo(f, "Juntar caja", (
        "const sinVacios = n => $(n).all().map(i => i.json).filter(o => Object.keys(o).length);\n"
        "return [{ json: { mes: hoy.slice(0, 7), movimientos: sinVacios('Leer caja'), clientes: sinVacios('Leer clientes (Contador)') } }];"),
        pos=(f.x, f.y)); f.x += 240
    co = claude(f, "Contador", "contador", "={{ JSON.stringify($json) }}", pos=(f.x, f.y)); f.x += 240
    i1 = informe("Contador", "r.alertas ? r.alertas.join(' | ') : (r.texto || '')"); f.x += 240
    g1 = guardar_hoja(f, "Guardar informe Contador", "Informes", (f.x, f.y))
    f.cadena(c, caja, cli1, j1, co, i1, g1)

    # Posventa
    f.y = 0
    f.x = x0
    sop = leer_hoja(f, "Leer soporte", "Soporte", (f.x, f.y)); f.x += 240
    cli2 = leer_hoja(f, "Leer clientes (Posventa)", "Clientes", (f.x, f.y)); f.x += 240
    j2 = codigo(f, "Juntar soporte", (
        "const sinVacios = n => $(n).all().map(i => i.json).filter(o => Object.keys(o).length);\n"
        "return [{ json: { mes: hoy.slice(0, 7), casos: sinVacios('Leer soporte'), clientes: sinVacios('Leer clientes (Posventa)') } }];"),
        pos=(f.x, f.y)); f.x += 240
    po = claude(f, "Posventa", "posventa", "={{ JSON.stringify($json) }}", pos=(f.x, f.y)); f.x += 240
    i2 = informe("Posventa", "(r.clientes || []).map(c => c.cliente + ': ' + c.estado).join(' | ') || (r.texto || '')"); f.x += 240
    g2 = guardar_hoja(f, "Guardar informe Posventa", "Informes", (f.x, f.y))
    f.cadena(c, sop, cli2, j2, po, i2, g2)

    # Marketing
    f.y = 300
    f.x = x0
    cli3 = leer_hoja(f, "Leer clientes (Marketing)", "Clientes", (f.x, f.y)); f.x += 240
    cl = codigo(f, "Clientes reales", (
        "const c = $input.all().map(i => i.json).filter(o => o.nombre);\n"
        "return c.length ? c.map(json => ({ json })) : [{ json: { sin_clientes: true } }];"), pos=(f.x, f.y)); f.x += 240
    si = f.nodo("¿Hay clientes?", "n8n-nodes-base.if", 2.2, {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
            "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ $json.sin_clientes === true }}", "rightValue": "",
                            "operator": {"type": "boolean", "operation": "false", "singleValue": True}}],
            "combinator": "and"},
        "options": {}}, (f.x, f.y)); f.x += 240
    mc = claude(f, "Marketing para Clientes", "marketing_clientes", "={{ JSON.stringify($json) }}",
                pos=(f.x, f.y - 120)); f.x += 240
    jm = codigo(f, "Juntar para la gerente", (
        "let propuestas = [];\n"
        "try { propuestas = $('Marketing para Clientes').all().map(i => leer(i.json)); } catch (e) {}\n"
        "return [{ json: { mes: hoy.slice(0, 7), propuestas_de_marketing_para_clientes: propuestas,\n"
        "  resultados_de_clientes: 'Todavía no hay resultados cargados.' } }];"), pos=(f.x, f.y)); f.x += 240
    ge = claude(f, "Gerente de Marketing", "marketing", "={{ JSON.stringify($json) }}", max_tokens=8000,
                pos=(f.x, f.y)); f.x += 240
    i3 = informe("Marketing", "(r.contenido_scaling || []).map(c => c.idea).join(' | ') || (r.texto || '')"); f.x += 240
    g3 = guardar_hoja(f, "Guardar informe Marketing", "Informes", (f.x, f.y))
    f.cadena(c, cli3, cl, si)
    f.unir(si, mc, 0)
    f.unir(si, jm, 1)
    f.cadena(mc, jm, ge, i3, g3)

    # La segunda lectura de clientes corre una sola vez, no una por fila de la primera.
    for n in f.nodos:
        if n["name"].startswith("Leer clientes (") and n["name"] != "Leer clientes (Marketing)":
            n["executeOnce"] = True
    f.guardar("2_informes_del_mes.json")


# --- 3 y 4. Chatbots ---

def chatbot(archivo, titulo, agente, pestana_contexto, armar_contexto, pestana_log, fila_log):
    f = Flujo(titulo, (
        f"## {titulo.split(' - ')[1]}\n"
        "Modo práctica: tocá **Open chat** abajo y escribile como si fueras un cliente.\n"
        "1. En **Config** pegá el link de tu planilla.\n"
        "2. Elegí tus credenciales en cada nodo.\n"
        f"Cada mensaje queda guardado en la pestaña **{pestana_log}**. Nadie de afuera lo ve hasta que lo conectes a WhatsApp."))
    t = f.nodo("Mensaje del chat", "@n8n/n8n-nodes-langchain.chatTrigger", 1.1, {"options": {}},
               webhookId=str(uuid.uuid4()))
    c = config(f)
    ctx = leer_hoja(f, f"Leer {pestana_contexto}", pestana_contexto)
    hist = leer_hoja(f, "Leer conversación", pestana_log)
    arm = codigo(f, "Armar mensaje", (
        "const msg = $('Mensaje del chat').first().json;\n"
        f"const contexto = $('Leer {pestana_contexto}').all().map(i => i.json).filter(o => Object.keys(o).length);\n"
        "const previos = $('Leer conversación').all().map(i => i.json).filter(o => o.sesion === msg.sessionId).slice(-10);\n"
        "const conversacion = previos.map(p => 'Cliente: ' + p.mensaje + '\\nVos: ' + p.respuesta).join('\\n\\n');\n"
        f"{armar_contexto}\n"
        "return [{ json: { system, mensaje: (conversacion ? 'Conversación hasta ahora:\\n' + conversacion + '\\n\\n' : '') + 'Nuevo mensaje: ' + msg.chatInput } }];"))
    cl = claude(f, "Claude", agente, "={{ $json.mensaje }}", max_tokens=2000, system="={{ $json.system }}")
    le = codigo(f, "Leer respuesta", (
        "const r = leer($json);\n"
        "const msg = $('Mensaje del chat').first().json;\n"
        f"return [{{ json: {fila_log} }}];"))
    g = guardar_hoja(f, "Guardar conversación", pestana_log)
    resp = f.nodo("Responder", "n8n-nodes-base.set", 3.4, {
        "mode": "manual",
        "assignments": {"assignments": [{"id": str(uuid.uuid4()), "name": "output",
                                         "value": "={{ $('Leer respuesta').first().json.respuesta }}",
                                         "type": "string"}]},
        "options": {}})
    # Leer las dos pestañas una sola vez por mensaje.
    for n in f.nodos:
        if n["name"] in (ctx, hist):
            n["executeOnce"] = True
    f.cadena(t, c, ctx, hist, arm, cl, le, g, resp)
    f.guardar(archivo)


def plantilla_js(texto):
    """Pasa las instrucciones a un texto de JavaScript donde ${...} se reemplaza por datos."""
    return "String.raw`" + texto.replace("```", "bloques de código").replace("`", "'") + "`"


def chatbots():
    soporte = instrucciones("chatbot_soporte").replace("{{FAQ}}", "${faq}").replace("{{CLIENTE}}", "${cliente}")
    chatbot("3_chatbot_soporte.json", "Scaling 3 - Chatbot de soporte", "chatbot_soporte", "FAQ",
            "const faq = contexto.map(p => 'P: ' + p.pregunta + '\\nR: ' + p.respuesta).join('\\n\\n') || 'Todavía no hay preguntas cargadas.';\n"
            "const cliente = 'Sin dato. Si no sabés de qué comercio es, preguntale el nombre.';\n"
            f"const system = {plantilla_js(soporte)};",
            "Soporte",
            "{ fecha: new Date().toISOString(), sesion: msg.sessionId, mensaje: msg.chatInput, respuesta: r.respuesta || r.texto, resuelto: r.resuelto, derivar_a_lucho: r.derivar_a_lucho, resumen_para_lucho: r.resumen_para_lucho }")
    leads = instrucciones("chatbot_leads").replace("{{INFO_SCALING}}", "${info}")
    chatbot("4_chatbot_leads.json", "Scaling 4 - Chatbot de leads", "chatbot_leads", "Info",
            "const info = contexto.map(p => p.texto).join('\\n') || 'Sin información cargada.';\n"
            f"const system = {plantilla_js(leads)};",
            "Leads",
            "{ fecha: new Date().toISOString(), sesion: msg.sessionId, mensaje: msg.chatInput, respuesta: r.respuesta || r.texto, lead_completo: r.lead_completo, pide_persona: r.pide_persona, ...(r.lead || {}) }")


# --- 5. Revisión de seguridad por oferta ---

def seguridad():
    f = Flujo("Scaling 5 - Revisión de seguridad por oferta", (
        "## Revisión de seguridad\n"
        "Se corre una vez por tipo de oferta, a mano.\n"
        "1. En **Config** pegá el link de tu planilla.\n"
        "2. En **Oferta a revisar** escribí la oferta y cómo la armamos.\n"
        "3. **Execute workflow**. El resultado queda en **Informes**."))
    a = f.nodo("Probar a mano", "n8n-nodes-base.manualTrigger", 1, {})
    c = config(f, [("oferta", "turnos online", "string"),
                   ("como_la_armamos", "Completar: qué herramienta usamos, dónde se guardan los datos y quién accede.", "string")])
    cl = claude(f, "Seguridad", "seguridad",
                "=Oferta: {{ $json.oferta }}\nCómo la armamos: {{ $json.como_la_armamos }}")
    i = codigo(f, "Armar informe", (
        "const r = leer($json);\n"
        "return [{ json: { fecha: hoy, agente: 'Seguridad: ' + (r.oferta || ''), resumen: (r.se_puede_vender ? 'Se puede vender. ' : 'No se puede vender todavía. ') + (r.motivo || r.texto || ''), detalle: celda(JSON.stringify(r)) } }];"))
    g = guardar_hoja(f, "Guardar informe", "Informes")
    f.cadena(a, c, cl, i, g)
    f.guardar("5_revision_de_seguridad.json")


# --- 6. Contrato de cliente ---

def contrato():
    f = Flujo("Scaling 6 - Contrato de cliente", (
        "## Contrato de cliente\n"
        "Se corre a mano cuando un comercio acepta la propuesta.\n"
        "1. En **Config** pegá el link de tu planilla y completá lo que acordaste con el cliente.\n"
        "2. Elegí tus credenciales en cada nodo.\n"
        "3. **Execute workflow**. El borrador queda en **Contratos**. Antes de firmar, que lo revise un abogado."))
    a = f.nodo("Probar a mano", "n8n-nodes-base.manualTrigger", 1, {})
    c = config(f, [("comercio", "Nombre del comercio", "string"),
                   ("oferta", "turnos online", "string"),
                   ("instalacion_ars", "Completar", "string"),
                   ("abono_mensual_ars", "Completar", "string"),
                   ("forma_de_pago", "Completar: por ejemplo, transferencia del 1 al 10 de cada mes", "string"),
                   ("lo_acordado", "Completar: qué se entrega, plazos y lo que hablaron", "string")])
    cl = claude(f, "Legal - Contrato", "legal_contrato", (
        "={{ JSON.stringify({ comercio: $json.comercio, oferta: $json.oferta, instalacion_ars: $json.instalacion_ars, "
        "abono_mensual_ars: $json.abono_mensual_ars, forma_de_pago: $json.forma_de_pago, lo_acordado: $json.lo_acordado }) }}"),
        max_tokens=16000)
    co = codigo(f, "Armar contrato", (
        "const r = leer($json);\n"
        "return [{ json: { fecha: hoy, comercio: $('Config').first().json.comercio,\n"
        "  contrato_borrador: celda(r.contrato_borrador || r.texto), falta_completar: celda(JSON.stringify(r.falta_completar || [])),\n"
        "  riesgos: celda(JSON.stringify(r.riesgos || [])), me_excede: celda(JSON.stringify(r.me_excede || [])) } }];"))
    g = guardar_hoja(f, "Guardar contrato", "Contratos")
    f.cadena(a, c, cl, co, g)
    f.guardar("6_contrato_de_cliente.json")


# --- 7. Ver adelantos ---

def ver_adelantos():
    f = Flujo("Scaling 7 - Ver adelantos", (
        "## Ver adelantos\n"
        "Un link para abrir en el celular los adelantos y mostrárselos al comercio.\n"
        "1. En **Config** pegá el link de tu planilla y elegí tu credencial de Google.\n"
        "2. En **Ver adelantos** elegí una credencial *Basic Auth* con un usuario y contraseña que inventes vos: el link los va a pedir.\n"
        "3. Tocá **Publish** y copiá la *Production URL* de **Ver adelantos**. Abrila en el celular: muestra la lista de comercios y tocás uno."))
    w = f.nodo("Ver adelantos", "n8n-nodes-base.webhook", 2.1, {
        "httpMethod": "GET", "path": "adelantos", "authentication": "basicAuth",
        "responseMode": "responseNode", "options": {}}, webhookId=str(uuid.uuid4()))
    c = config(f)
    le = leer_hoja(f, "Leer adelantos", "Adelantos")
    pa = codigo(f, "Armar página", (
        "const pedido = $('Ver adelantos').first().json.query.comercio;\n"
        "const ultimos = new Map();\n"
        "for (const i of $input.all()) if (i.json.comercio) ultimos.set(i.json.comercio, i.json);\n"
        "const elegido = ultimos.get(pedido);\n"
        "if (elegido && elegido.html) return [{ json: { html: elegido.html } }];\n"
        "const esc = s => String(s ?? '').replace(/[&<>\"']/g, c => '&#' + c.charCodeAt(0) + ';');\n"
        "const lista = [...ultimos.values()].reverse().map(a =>\n"
        "  `<li><a href='?comercio=${encodeURIComponent(a.comercio)}'>${esc(a.comercio)}</a><br><small>${esc(a.oferta)} · ${esc(a.fecha)}</small></li>`).join('');\n"
        "return [{ json: { html: `<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'><title>Adelantos de Scaling</title>\n"
        "<style>body{font-family:sans-serif;margin:16px;line-height:1.4}li{margin:14px 0}a{font-size:1.1em}</style></head>\n"
        "<body><h1>Adelantos</h1>${lista ? '<ul>' + lista + '</ul>' : '<p>Todavía no hay adelantos. Se arman cuando corre la mesa chica.</p>'}</body></html>` } }];"))
    r = f.nodo("Mostrar página", "n8n-nodes-base.respondToWebhook", 1.4, {
        "respondWith": "text", "responseBody": "={{ $json.html }}",
        "options": {"responseHeaders": {"entries": [{"name": "Content-Type", "value": "text/html; charset=utf-8"}]}}})
    f.cadena(w, c, le, pa, r)
    f.guardar("7_ver_adelantos.json")


# --- Planilla modelo ---

def planilla():
    import csv
    wb = Workbook()
    wb.remove(wb.active)
    comercios = list(csv.DictReader(open(RAIZ / "buscador" / "comercios.csv", encoding="utf-8")))
    for nombre, columnas in PESTANAS.items():
        ws = wb.create_sheet(nombre)
        ws.append(columnas)
        if nombre == "Comercios":
            for c in comercios:
                ws.append([c.get(k, "") for k in columnas])
        if nombre == "Info":
            ws.append([INFO_SCALING])
    wb.save(SALIDA / "planilla_scaling.xlsx")



if __name__ == "__main__":
    mesa_chica()
    informes()
    chatbots()
    seguridad()
    contrato()
    ver_adelantos()
    planilla()
    print("Listo:", ", ".join(sorted(p.name for p in SALIDA.iterdir() if p.suffix in (".json", ".xlsx"))))
