from prompts import NORMA_MONEDA, REGLAS_COMUNES

DATOS_VENTAS_PRUEBA = """producto,cantidad,total
Pan frances,80,40.00
Croissant,25,50.00
Pan integral,15,11.25"""

PREGUNTA = "¿Cuál fue el comportamiento de las ventas del día y qué recomendarías?"

SISTEMA_BASE = (
    "Eres Pandito AI, analista de ventas de la Panadería Los Andes. "
    "Analizas únicamente los datos proporcionados, no inventas cifras ni "
    "productos, y dejas la decisión final para el encargado. "
    + REGLAS_COMUNES + " " + NORMA_MONEDA
)

_EJEMPLO_1 = (
    "Datos:\nproducto,cantidad,total\nAlfajor,40,80.00\nEmpanada,10,15.00\n"
    f"Pregunta: {PREGUNTA}\n"
    "Respuesta: Se vendieron 50 unidades por un total de S/ 95.00. El producto "
    "más vendido fue Alfajor con 40 unidades. Se recomienda mantener el nivel "
    "de producción de Alfajor y evaluar una promoción para Empanada."
)

_EJEMPLO_2 = (
    "Datos:\nproducto,cantidad,total\nTorta de chocolate,5,17.50\nPan integral,30,22.50\n"
    f"Pregunta: {PREGUNTA}\n"
    "Respuesta: Se vendieron 35 unidades por un total de S/ 40.00. Pan integral "
    "lideró en unidades vendidas. Se recomienda reforzar su producción y revisar "
    "el precio de Torta de chocolate por su baja rotación."
)

_CASO_A_RESOLVER = (
    f"Datos de ventas del día:\n{DATOS_VENTAS_PRUEBA}\n\nPregunta: {PREGUNTA}"
)

SHOT_PROMPTS = {
    "zero_shot": {
        "nombre": "Zero-Shot",
        "sistema": SISTEMA_BASE,
        "usuario": _CASO_A_RESOLVER,
    },
    "one_shot": {
        "nombre": "One-Shot",
        "sistema": SISTEMA_BASE,
        "usuario": f"Ejemplo:\n{_EJEMPLO_1}\n\nAhora resuelve este caso:\n{_CASO_A_RESOLVER}",
    },
    "few_shot": {
        "nombre": "Few-Shot",
        "sistema": SISTEMA_BASE,
        "usuario": (
            f"Ejemplo 1:\n{_EJEMPLO_1}\n\nEjemplo 2:\n{_EJEMPLO_2}\n\n"
            f"Ahora resuelve este caso:\n{_CASO_A_RESOLVER}"
        ),
    },
}