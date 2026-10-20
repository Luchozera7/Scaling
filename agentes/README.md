# Mesa chica de agentes

Cada agente es un pedido a Claude con instrucciones fijas (el archivo `.md` de cada uno).
En n8n, cada agente es un nodo de Claude: las instrucciones van como "system prompt"
y como mensaje se le pasa el comercio (una fila de la planilla) más lo que dijeron los anteriores.

## Orden

1. `it_producto.md`: qué le falta al comercio, qué le ofrecemos y cómo se entrega de forma segura (fuga de prompts, datos, claves).
2. `marketing.md`: qué tan buen cliente es.
3. `finanzas.md`: presupuesto según las horas de desarrollo, implementación y mantenimiento, proyección a 3, 6 y 12 meses e impacto en nuestra caja.
4. `legal.md`: borrador de contrato, riesgos para el CEO y lo que necesita un abogado o contador.
5. `jefe_de_gabinete.md`: el gerente general. Revisa todo, elige como máximo 3, marca lo que no sirve y trae el próximo paso para el CEO.

Los agentes 1 a 3 se corren una vez por comercio. Legal solo se corre con los 5 que mejor suman puntaje entre IT, Marketing y Finanzas (la cuenta la hace n8n, sin Claude). El Jefe de Gabinete se corre una vez con todo junto.

Aparte, `contador.md` le lleva las cuentas a Scaling: se corre una vez por mes con la pestaña "Caja" de la planilla, y su resumen se lo pasa a Finanzas y al Jefe de Gabinete.

Para empezar alcanza con IT y Producto y el Jefe de Gabinete.

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

Cada agente agrega sus propios campos (por ejemplo `oferta` o `presupuesto`). Legal, el Contador y el Jefe de Gabinete usan su propio formato.
Si un dato no se sabe, el agente pone "sin dato" y no lo inventa.
