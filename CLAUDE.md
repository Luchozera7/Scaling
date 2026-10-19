# CLAUDE.md

Instrucciones para Claude cuando trabaja en este repo.

## El proyecto

Scaling es una mini empresa de agentes de IA. Busca comercios chicos de Pablo Podestá / Tres de Febrero (Argentina), analiza qué les falta (turnos online, web, chatbot de WhatsApp/Instagram, inventario y caja) y arma propuestas. Una mesa chica de agentes (Prospección, Marketing, IT y Producto, Finanzas, Legal y un Jefe de Gabinete) filtra y rankea. Al CEO le llega una propuesta formal con los 2 o 3 mejores comercios. El CEO decide y contacta él mismo por WhatsApp.

Stack previsto: n8n, Claude API, Google Sheets, OpenStreetMap y la API oficial de Google Places.

## Con quién trabajás

Lucho, el dueño, no programa. Trabaja todo desde la app de Claude y está aprendiendo n8n.

- Hablale en castellano rioplatense, simple y sin jerga. Si un término técnico es inevitable, explicalo en una línea.
- Contale qué cambió y qué puede hacer él ahora, no cómo está hecho por dentro.
- Si algo tiene varias opciones, elegí la más razonable, decile cuál elegiste y por qué, y seguí. Preguntá solo cuando la decisión cambie lo que él va a ver, cueste plata o no se pueda deshacer.
- Diseño de a pasos: primero un diagrama o una explicación corta, después el código.

## Cómo escribir código

**Simple primero.** Lo mínimo que resuelva lo pedido. Nada de funciones extra, abstracciones para un solo uso ni configuraciones que nadie pidió. Si 200 líneas pueden ser 50, reescribilo. Lucho tiene que poder mantener esto con ayuda de Claude, así que menos piezas es mejor.

**Cambios quirúrgicos.** Tocá solo lo necesario para el pedido. No "mejores" código, comentarios ni formato que no tienen que ver. Respetá el estilo que ya existe. Si ves algo roto o muerto que no es parte del pedido, avisalo pero no lo borres. Sí borrá lo que tu propio cambio dejó sin uso.

**Terminado = verificado.** Antes de empezar, convertí el pedido en algo comprobable. Por ejemplo, "hacé el scraper" pasa a ser "trae 20 comercios de Podestá con nombre, rubro y teléfono en la planilla". Probalo de verdad antes de decir que está listo y mostrale a Lucho el resultado (una muestra de datos, una captura, la salida).

## Reglas fijas

- **Nunca** pongas claves, tokens ni contraseñas en el código ni en el chat. Van en las variables de entorno.
- No scrapees Google Maps ni Instagram. Usá las APIs oficiales u OpenStreetMap.
- Nada de envíos masivos (mails, WhatsApp, llamadas). Los agentes proponen y Lucho contacta.
- Cada propuesta de los agentes trae números que se puedan comprobar (costos, precio, ahorro esperado) y de dónde salió cada dato.
