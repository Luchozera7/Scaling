# CLAUDE.md

Instrucciones para Claude cuando trabaja en este repo.

## El proyecto

Scaling es una mini empresa de agentes de IA. Busca comercios chicos de Pablo Podestá / Tres de Febrero (Argentina), analiza qué les falta (turnos online, web, chatbot de WhatsApp/Instagram, inventario y caja) y arma propuestas. Una mesa chica de agentes (Prospección, Marketing, IT y Producto, Finanzas, Legal y un Jefe de Gabinete) filtra y rankea. Al CEO le llega una propuesta formal con los 2 o 3 mejores comercios. El CEO decide y contacta él mismo por WhatsApp.

Stack previsto: n8n, Claude API, Google Sheets, OpenStreetMap y la API oficial de Google Places.

## Con quién trabajás

Lucho es el dueño y el CEO del proyecto. Las ideas y la dirección son suyas, y el trabajo de Claude es convertirlas en código que funcione. Lo hacen en equipo: Claude propone, Lucho decide.

- **Las decisiones de peso las toma Lucho.** Qué se construye, cómo funciona para el usuario o el comercio, qué herramienta o servicio se usa, todo lo que cueste plata y todo lo que no se pueda deshacer. Presentale las opciones con tu recomendación y por qué, y esperá su respuesta antes de avanzar en eso.
- Los detalles técnicos internos (nombres, estructura del código, cómo se prueba) los resolvés vos y se los contás.
- Si ves una forma mejor de hacer lo que pidió, decíselo con argumentos. No cambies su idea por tu cuenta.
- Él trabaja desde la app de Claude, está aprendiendo n8n y no escribe código. Hablale en castellano rioplatense y sin jerga. Si un término técnico es inevitable, explicalo en una línea.
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
