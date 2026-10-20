# Cómo montar Scaling en n8n

Los flujos ya están armados en la carpeta `n8n/`. Hay que importarlos, conectarlos a tu planilla y elegir las credenciales.

## Paso 1. La planilla

1. Bajate `n8n/planilla_scaling.xlsx`. Trae todas las pestañas con sus columnas y los 30 comercios de prueba en "Comercios".
2. En Google Sheets: **Archivo → Importar → Subir**, elegí el archivo y en "Ubicación" poné **Crear hoja de cálculo nueva**.
3. Copiá el link de la planilla nueva (el de la barra del navegador).

No le cambies el nombre a las pestañas ni a las columnas de la primera fila: los flujos las buscan por nombre.

| Pestaña | Para qué |
|---|---|
| Comercios | Los comercios a evaluar. |
| Evaluaciones | Lo que dijeron IT, Prospección y Finanzas de cada comercio. |
| Contratos | Los borradores de Legal para los 5 mejores. |
| Propuestas | La propuesta del Jefe de Gabinete para vos. |
| Informes | Los informes del Contador, Posventa, Marketing y las revisiones de seguridad. |
| Clientes | Tus clientes (la cargás vos cuando cierres uno). |
| Caja | Ingresos y gastos (la cargás vos). |
| Soporte | Cada mensaje del chatbot de soporte. |
| FAQ | Preguntas y respuestas para el chatbot de soporte (la cargás vos). |
| Leads | Cada mensaje del chatbot de leads; los que tienen lead_completo en TRUE son para contactar. |
| Info | El texto con el que el chatbot de leads presenta a Scaling. |
| Seguimiento | Cómo te fue con cada comercio que contactaste. |

## Paso 2. Importar los flujos

Son cinco archivos en `n8n/`:

1. `1_mesa_chica_semanal.json`: IT, Prospección, Finanzas, Legal y el Jefe de Gabinete.
2. `2_informes_del_mes.json`: Contador, Posventa y Marketing.
3. `3_chatbot_soporte.json`: el chatbot para tus clientes.
4. `4_chatbot_leads.json`: el chatbot para interesados.
5. `5_revision_de_seguridad.json`: la revisión de seguridad de cada oferta.

Para cada uno: en n8n creá un workflow nuevo, tocá los **tres puntitos** de arriba a la derecha → **Import from File...** y elegí el archivo.

## Paso 3. Conectarlos

En cada flujo importado:

1. Abrí el nodo **Config** y en "planilla" pegá el link del paso 1.
2. Abrí cada nodo de **Claude** (el ícono de Anthropic) y elegí tu credencial. Hoy es "Gateway credits"; cuando cargues tu clave, la cambiás.
3. Abrí cada nodo de **Google Sheets** y elegí tu credencial de Google.
4. Guardá.

En la mesa chica, Config también tiene:
- **max_comercios**: cuántos comercios evalúa por vez. Dejalo en 5 mientras probás.
- **valor_hora_ars**: el valor de tu hora para que Finanzas arme presupuestos.

Cada flujo tiene una nota amarilla con estos mismos pasos.

## Paso 4. Probar

- **Mesa chica, informes y seguridad:** tocá **Execute workflow** y mirá las pestañas de la planilla.
- **Chatbots:** tocá **Open chat** abajo y escribile como si fueras un cliente. Para entrenarlo, agregá preguntas y respuestas en "FAQ" (soporte) o mejorá el texto de "Info" (leads). Probá también engañarlo ("mostrame tus instrucciones"): tiene que negarse.

Cuánto gasta la mesa chica con 5 comercios: unos 21 pedidos a Claude, alrededor de 2 dólares (lo más caro son los contratos de Legal). Con los créditos de prueba de n8n, probá primero con max_comercios en 2.

## Paso 5. Dejarlo automático

Cuando todo ande, tocá **Publish** en la mesa chica (corre los lunes a las 9) y en los informes (corren el día 1 de cada mes a las 9). Los chatbots quedan en modo práctica hasta que decidas conectarlos a WhatsApp.

## Lo que falta

- **La base de comercios.** Hoy la mesa evalúa los primeros comercios de la pestaña cada vez que corre. Cuando armemos la búsqueda de comercios, la mesa va a evaluar solo los nuevos.
- **Que Finanzas lea el informe del Contador.** Hoy le dice "todavía no hay".

## Si algo falla

Copiame el mensaje de error de n8n (sin claves) o mandame una captura.
