# Mesa chica de agentes

Cada agente es un pedido a Claude con instrucciones fijas (el archivo `.md` de cada uno).
En n8n, cada agente es un nodo de Claude: las instrucciones van como "system prompt"
y como mensaje se le pasa el comercio (una fila de la planilla) más lo que dijeron los anteriores.

## La mesa chica (una vez por semana, con los comercios nuevos)

1. `it_producto.md`: qué le falta al comercio y qué le ofrecemos.
2. `prospeccion.md`: qué tan buen cliente es.
3. `finanzas.md`: presupuesto según las horas de desarrollo, implementación y mantenimiento, proyección a 3, 6 y 12 meses e impacto en nuestra caja.
4. `legal.md`: borrador de contrato, riesgos para el CEO y lo que necesita un abogado o contador.
5. `jefe_de_gabinete.md`: el gerente general. Revisa todo, elige como máximo 3, marca lo que no sirve y trae el próximo paso para el CEO.

Los agentes 1 a 3 se corren una vez por comercio. Legal solo se corre con los 5 que mejor suman puntaje entre IT, Prospección y Finanzas (la cuenta la hace n8n, sin Claude). El Jefe de Gabinete se corre una vez con todo junto.

## Una vez por tipo de oferta

- `seguridad.md` (IT y Producto): revisión de seguridad de cada oferta (fuga de prompts, manipulación, datos, claves). Se repite solo si la oferta cambia.

## Una vez por mes

- `contador.md` (bajo Finanzas): lleva las cuentas con la pestaña "Caja". Su resumen va a Finanzas y al Jefe de Gabinete.
- `posventa.md`: cuida a los clientes que ya pagan, con la pestaña "Soporte". Su resumen va al Jefe de Gabinete.
- `marketing.md` (gerente): contenido para mostrar lo que hace Scaling, y revisa y aprueba lo de Marketing para Clientes.
- `marketing_clientes.md` (bajo la gerente de Marketing): propuestas de marketing para cada cliente.

## Chatbots (responden en el momento)

- `chatbot_soporte.md`: atiende a los clientes. Responde con el FAQ y deriva a Lucho lo que no puede resolver.
- `chatbot_leads.md`: atiende a comercios interesados, cuenta qué hacemos y junta los datos para que Lucho los contacte.

`{{FAQ}}`, `{{CLIENTE}}` e `{{INFO_SCALING}}` se reemplazan en n8n con los datos de la planilla.

Cómo montar todo en n8n: `guia_n8n.md`.

## Qué devuelve cada uno

Siempre JSON, con el mismo formato base, para que n8n lo pueda guardar en la planilla:

```json
{
  "agente": "IT y Producto",
  "comercio": "Studio B",
  "puntaje": 7,
  "motivo": "Una o dos oraciones.",
  "datos": [
    {"dato": "No tiene web cargada", "fuente": "OpenStreetMap, https://www.openstreetmap.org/node/..."}
  ]
}
```

Cada agente agrega sus propios campos (por ejemplo `oferta` o `presupuesto`). Legal, el Contador, Posventa, Marketing, el Jefe de Gabinete y los chatbots usan su propio formato.
Si un dato no se sabe, el agente pone "sin dato" y no lo inventa.
