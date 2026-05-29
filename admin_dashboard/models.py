from __future__ import annotations

from django.db import models


class DashboardStat(models.Model):
    """
    관리자 대시보드 확장용 placeholder 모델.
    """

    name = models.CharField(max_length=80, unique=True)
    value = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"

    class Meta:
        verbose_name = "Dashboard Stat"
        verbose_name_plural = "Dashboard Stats"
