import logging

logger = logging.getLogger(__name__)


def send_deadline_alerts():
    """
    HU-28: Busca casos próximos a vencer y genera notificaciones
    con email para estudiantes y profesores responsables.
    """
    from cases.services import generate_deadline_alerts

    try:
        created = generate_deadline_alerts(days_ahead=3)
        logger.info(
            "Deadline alerts job finished. Notifications created: %d",
            created,
        )
    except Exception as exc:
        logger.error("Deadline alerts job failed: %s", exc)