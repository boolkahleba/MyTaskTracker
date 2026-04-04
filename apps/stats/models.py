from django.db import models


class BoardStatsSnapshot(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Снимок статистики'
        verbose_name_plural = 'Снимки статистики'
        db_table = 'Board_stats_snapshot'