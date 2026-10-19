"""Busca peluquerías, barberías y centros de estética en Tres de Febrero
usando OpenStreetMap (Overpass API, gratis y sin claves).

Guarda una planilla CSV ordenada por cercanía a Pablo Podestá.

Uso:  python3 buscador/buscar_comercios.py
"""

import csv
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
PODESTA = (-34.5833, -58.6167)  # centro aproximado de Pablo Podestá
CANTIDAD = 30
SALIDA = Path(__file__).parent / "comercios.csv"

# Todo el partido de Tres de Febrero. En OpenStreetMap las barberías suelen
# figurar como shop=hairdresser, y la estética como shop=beauty.
CONSULTA = """
[out:json][timeout:60];
area["name"~"Tres de Febrero"]["boundary"="administrative"]["admin_level"="5"]->.zona;
nwr["shop"~"^(hairdresser|beauty|barber|cosmetics)$"](area.zona);
out center tags;
"""

RUBROS = {
    "hairdresser": "Peluquería",
    "barber": "Barbería",
    "beauty": "Estética",
    "cosmetics": "Estética",
}


def distancia_km(lat, lon):
    lat1, lon1 = map(math.radians, PODESTA)
    lat2, lon2 = math.radians(lat), math.radians(lon)
    a = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def a_fila(elemento):
    t = elemento.get("tags", {})
    lat = elemento.get("lat") or elemento.get("center", {}).get("lat")
    lon = elemento.get("lon") or elemento.get("center", {}).get("lon")
    rubro = RUBROS.get(t.get("shop"), t.get("shop"))
    if t.get("hairdresser") == "barber":
        rubro = "Barbería"
    direccion = " ".join(x for x in (t.get("addr:street"), t.get("addr:housenumber")) if x)
    return {
        "nombre": t.get("name", ""),
        "rubro": rubro,
        "direccion": direccion,
        "localidad": t.get("addr:city", ""),
        "telefono": t.get("phone") or t.get("contact:phone") or t.get("contact:whatsapp") or "",
        "web": t.get("website") or t.get("contact:website") or "",
        "instagram": t.get("contact:instagram", ""),
        "distancia_km": round(distancia_km(lat, lon), 1),
        "fuente": f"https://www.openstreetmap.org/{elemento['type']}/{elemento['id']}",
    }


def main():
    datos = urllib.parse.urlencode({"data": CONSULTA}).encode()
    pedido = urllib.request.Request(OVERPASS_URL, data=datos,
                                    headers={"User-Agent": "Scaling-buscador/1.0"})
    with urllib.request.urlopen(pedido, timeout=90) as r:
        elementos = json.load(r)["elements"]

    filas = [a_fila(e) for e in elementos if e.get("tags", {}).get("name")]
    filas.sort(key=lambda f: f["distancia_km"])
    filas = filas[:CANTIDAD]

    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()) if filas else ["nombre"])
        escritor.writeheader()
        escritor.writerows(filas)

    con_tel = sum(1 for f in filas if f["telefono"])
    print(f"OpenStreetMap devolvió {len(elementos)} comercios del rubro en Tres de Febrero.")
    print(f"Guardé los {len(filas)} más cercanos a Podestá en {SALIDA}")
    print(f"Con teléfono: {con_tel} de {len(filas)}")
    if not filas:
        sys.exit(1)


if __name__ == "__main__":
    main()
