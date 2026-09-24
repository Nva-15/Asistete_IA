import re
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

NOTA_DATOS_FICTICIOS = (
    "Nota: los datos utilizados en este reporte son ficticios y fueron "
    "creados exclusivamente para validar el funcionamiento del prototipo."
)


class ReportePDF(FPDF):
    titulo_reporte = ""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Panaderia Los Andes", ln=1, align="C")
        self.set_font("Helvetica", "", 11)
        self.cell(0, 6, self.titulo_reporte, ln=1, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(
            0, 10,
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} "
            f"- Pandito AI - Pagina {self.page_no()}",
            align="C"
        )


def _escribir_parrafos(pdf, contenido, alto=6):
    texto = contenido.encode("latin-1", "ignore").decode("latin-1")
    for parrafo in texto.split("\n"):
        if parrafo.strip():
            pdf.multi_cell(0, alto, parrafo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.ln(alto / 2)


def _dividir_fila_md(linea):
    linea = linea.strip().strip("|")
    return [c.strip() for c in linea.split("|")]


def _es_separador_md(linea):
    partes = _dividir_fila_md(linea)
    return bool(partes) and all(re.match(r"^:?-{2,}:?$", p) for p in partes)


def _escribir_tabla(pdf, tabla_datos, titulo="Datos"):
    """Dibuja tabla_datos = {'columnas': [...], 'filas': [[...], ...]} como tabla real."""
    if titulo:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(text_align="CENTER", line_height=6) as table:
        fila = table.row()
        for col in tabla_datos["columnas"]:
            fila.cell(str(col))
        for datos_fila in tabla_datos["filas"]:
            fila = table.row()
            for valor in datos_fila:
                fila.cell(str(valor))
    pdf.ln(4)

def _escribir_contenido_ia(pdf, contenido, alto=6):
    """Escribe texto de la IA, detectando y dibujando tablas markdown como tablas reales."""
    texto = contenido.encode("latin-1", "ignore").decode("latin-1")
    lineas = texto.split("\n")
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if "|" in linea and i + 1 < len(lineas) and _es_separador_md(lineas[i + 1]):
            columnas = _dividir_fila_md(linea)
            filas = []
            i += 2
            while i < len(lineas) and "|" in lineas[i]:
                filas.append(_dividir_fila_md(lineas[i]))
                i += 1
            fuente = pdf.font_size_pt
            _escribir_tabla(pdf, {"columnas": columnas, "filas": filas}, titulo=None)
            pdf.set_font("Helvetica", "", fuente)
        elif linea.strip():
            pdf.multi_cell(0, alto, linea, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
        else:
            pdf.ln(alto / 2)
            i += 1

def generar_pdf_reporte(titulo, contenido, tabla_datos=None, nota_datos_ficticios=True):
    """Convierte un reporte de texto (y opcionalmente una tabla) en PDF."""
    pdf = ReportePDF()
    pdf.titulo_reporte = titulo
    pdf.add_page()

    if tabla_datos and tabla_datos["filas"]:
        _escribir_tabla(pdf, tabla_datos)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Resumen generado por IA", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 11)
    _escribir_contenido_ia(pdf, contenido)

    if nota_datos_ficticios:
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, NOTA_DATOS_FICTICIOS, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())

def generar_pdf_comparacion(resultados, pregunta, datos):
    """Genera un PDF con las respuestas Zero/One/Few-Shot, una sección por técnica."""
    pdf = ReportePDF()
    pdf.titulo_reporte = "Comparacion Zero-Shot / One-Shot / Few-Shot"
    pdf.add_page()

    pdf.set_font("Helvetica", "I", 9)
    _escribir_parrafos(pdf, f"Pregunta: {pregunta}", alto=5)
    _escribir_parrafos(pdf, f"Datos:\n{datos}", alto=5)
    pdf.ln(3)

    for datos_tecnica in resultados.values():
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 7, datos_tecnica["nombre"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        _escribir_contenido_ia(pdf, datos_tecnica["respuesta"], alto=5)
        pdf.ln(4)

    return bytes(pdf.output())
