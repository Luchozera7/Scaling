# Mesa chica de agentes

Cada agente es un pedido a Claude con instrucciones fijas (el archivo `.md` de cada uno).
En n8n, cada agente es un nodo de Claude: las instrucciones van como "system prompt"
y como mensaje se le pasa el comercio (una fila de la planilla) más lo que dijeron los anteriores.

## Orden

1. `it_producto.md`: qué le falta al comercio y qué le ofrecemos.
2. `marketing.md`: qué tan buen cliente es.
3. `finanzas.md`: presupuesto según las horas de desarrollo, implementación y mantenimiento, y proyección a 3, 6 y 12 meses.
4. `jefe_de_gabinete.md`: recibe a todos los comercios evaluados, rankea y elige los 2 o 3 mejores.
5. `legal.md`: para los elegidos, arma el borrador de contrato, lista los riesgos para el CEO y avisa lo que necesita un abogado o contador.

Los agentes 1 a 3 se corren una vez por comercio. El 4 se corre una sola vez con todos juntos. El 5 solo con los elegidos, y su resultado va con la propuesta al CEO.

Para empezar alcanza con el 1 y el 4.

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

Cada agente agrega sus propios campos (por ejemplo `oferta` o `presupuesto`). Legal y el Jefe de Gabinete usan su propio formato.
Si un dato no se sabe, el agente pone "sin dato" y no lo inventa.
