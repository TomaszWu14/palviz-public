"""Odwiedzający wersję demonstracyjną (bramka core/demo_gate.py). Bez IP i user-agenta."""
from datetime import timedelta

from django.db import models
from django.utils import timezone

__all__ = ["DemoVisitor", "DEMO_VISITOR_RETAIN_DAYS", "purge_old_visitors"]

DEMO_VISITOR_RETAIN_DAYS = 90


class DemoVisitor(models.Model):
    first_name = models.CharField("imię", max_length=100)
    last_name = models.CharField("nazwisko", max_length=100)
    company = models.CharField("firma", max_length=100)
    created_at = models.DateTimeField("data wizyty", default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "odwiedzający demo"
        verbose_name_plural = "odwiedzający demo"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.company})"


def purge_old_visitors(now=None) -> int:
    """Usuwa wpisy starsze niż 90 dni (wołane przy zapisie i w zadaniu ui.gdpr_retention)."""
    cutoff = (now or timezone.now()) - timedelta(days=DEMO_VISITOR_RETAIN_DAYS)
    return DemoVisitor.objects.filter(created_at__lt=cutoff).delete()[0]
