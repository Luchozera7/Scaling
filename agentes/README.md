# Mesa chica de agentes

Cada agente es un pedido a Claude con instrucciones fijas (el archivo `.md` de cada uno).
En n8n, cada agente es un nodo de Claude: las instrucciones van como "system prompt"
y como mensaje se le pasa el comercio (una fila de la planilla) más lo que dijeron los anteriores.

## Orden

1. `it_producto.md`: qué le falta al comercio y qué le ofrecemos.
2. `marketing.md`: qué tan buen cliente es.
3. `finanzas.md`: costo, precio y margen. Puede vetar.
4. `legal.md`: si se le puede escribir y cómo. Puede vetar.
5. `jefe_de_gabinete.md`: recibe a todos los comercios evaluados, rankea y escribe la propuesta al CEO.

Los agentes 1 a 4 se corren una vez por comercio. El 5 se corre una sola vez con todos juntos.

Para empezar alcanza con el 1 y el 5.

## Qué devuelve cada uno

Siempre JSON, con el mismo formato base, para que n8n lo pueda guardar en la planilla:

```json
{
  "agente": "IT y Producto",
  "comercio": "Studio B",
  "puntaje": 7,
  "veto": false,
  "motivo": "Una o dos oraciones.",
  "datos": [
    {"dato": "No tiene web cargada", "fuente": "OpenStreetMap, https://www.openstreetmap.org/node/..."}
  ]
}
```

Cada agente agrega sus propios campos (por ejemplo `oferta` o `precio_mensual_ars`).
Si un dato no se sabe, el agente pone "sin dato" y no lo inventa.
