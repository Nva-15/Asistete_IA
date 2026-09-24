from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import atexit
import traceback

from automatizaciones import (
    auto_reporte_diario,
    auto_resumen_semanal,
    auto_alerta_stock,
    auto_sugerir_pedido,
    auto_prediccion_demanda,
    auto_horas_pico,
    auto_rentabilidad
)

# INSTANCIA GLOBAL
scheduler = BackgroundScheduler(timezone="America/Lima")

# INICIALIZACIÓN (idempotente)
def iniciar_scheduler():
    """
    Registra y arranca todas las tareas programadas.
    Es IDEMPOTENTE: si ya está corriendo, no hace nada y no lanza error.
    """
    # Guard 1: si ya está corriendo, salir silenciosamente
    if scheduler.running:
        print(f"♻️ Scheduler ya estaba activo ({len(scheduler.get_jobs())} tareas)")
        return

    try:
        # 1. Reporte diario a las 20:00
        scheduler.add_job(
            auto_reporte_diario,
            CronTrigger(hour=20, minute=0),
            id="reporte_diario",
            name="Reporte diario de ventas",
            replace_existing=True,
            misfire_grace_time=3600
        )

        # 2. Resumen semanal lunes 09:00
        scheduler.add_job(
            auto_resumen_semanal,
            CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="resumen_semanal",
            name="Resumen semanal gerencial",
            replace_existing=True,
            misfire_grace_time=3600
        )

        # 3. Alerta de stock cada 2 horas
        scheduler.add_job(
            auto_alerta_stock,
            IntervalTrigger(hours=2),
            id="alerta_stock",
            name="Alerta de stock crítico",
            replace_existing=True,
            misfire_grace_time=600
        )

        # 4. Sugerencia de pedido todos los días a las 07:00
        scheduler.add_job(
            auto_sugerir_pedido,
            CronTrigger(hour=7, minute=0),
            id="sugerir_pedido",
            name="Sugerencia de pedido a proveedores",
            replace_existing=True,
            misfire_grace_time=3600
        )

        # 5. Predicción de demanda todos los días a las 06:00
        scheduler.add_job(
            auto_prediccion_demanda,
            CronTrigger(hour=6, minute=0),
            id="prediccion_demanda",
            name="Predicción de demanda",
            replace_existing=True,
            misfire_grace_time=3600
        )

        # 6. Análisis de horas pico domingos a las 22:00
        scheduler.add_job(
            auto_horas_pico,
            CronTrigger(day_of_week="sun", hour=22, minute=0),
            id="horas_pico",
            name="Análisis de horas pico",
            replace_existing=True,
            misfire_grace_time=3600
        )

        # 7. Rentabilidad semanal los lunes a las 10:00
        scheduler.add_job(
            auto_rentabilidad,
            CronTrigger(day_of_week="mon", hour=10, minute=0),
            id="rentabilidad",
            name="Análisis de rentabilidad",
            replace_existing=True,
            misfire_grace_time=3600
        )

        # Guard 2: verificar otra vez por si otro hilo lo arrancó
        if not scheduler.running:
            scheduler.start()
            print(f"🚀 Scheduler iniciado a las {datetime.now().isoformat()}")
            print(f"📋 Tareas registradas: {[job.name for job in scheduler.get_jobs()]}")
            atexit.register(lambda: scheduler.shutdown(wait=False))
        else:
            print(f"♻️ Scheduler ya arrancado por otro hilo")

    except Exception as e:
        # No lanzar: silenciar cualquier error para no romper la app
        print(f"⚠️ Error al iniciar scheduler: {e}")
        traceback.print_exc()

# CONSULTAS
def listar_tareas():
    """Devuelve las tareas activas con su próxima ejecución."""
    tareas = []
    for job in scheduler.get_jobs():
        try:
            proxima = str(job.next_run_time) if job.next_run_time else "—"
        except Exception:
            proxima = "—"

        tareas.append({
            "id": job.id,
            "nombre": job.name,
            "próxima_ejecución": proxima,
            "estado": "activa" if scheduler.running else "detenida"
        })
    return tareas

def obtener_tarea(job_id):
    """Devuelve la tarea por id o None."""
    return scheduler.get_job(job_id)

# EJECUCIÓN MANUAL
def ejecutar_ahora(job_id):
    try:
        job = scheduler.get_job(job_id)
        if not job:
            print(f"⚠️ Tarea '{job_id}' no encontrada")
            return None
        return job.func()
    except Exception as e:
        print(f"❌ Error ejecutando {job_id}: {e}")
        traceback.print_exc()
        return None

# CONTROL DE TAREAS
def pausar_tarea(job_id):
    try:
        scheduler.pause_job(job_id)
        return True
    except Exception as e:
        print(f"Error al pausar {job_id}: {e}")
        return False


def reanudar_tarea(job_id):
    try:
        scheduler.resume_job(job_id)
        return True
    except Exception as e:
        print(f"Error al reanudar {job_id}: {e}")
        return False