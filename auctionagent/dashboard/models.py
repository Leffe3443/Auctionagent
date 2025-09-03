from django.db import models

# Create your models here.
from django.db import models

class AuctionScrapeRun(models.Model):
    created_at   = models.DateTimeField(auto_now_add=True)
    pages        = models.PositiveIntegerField(default=1)
    prompt       = models.TextField(blank=True, default="")      # AI prompt used (optional)
    items_found  = models.PositiveIntegerField(default=0)
    duration_ms  = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Run {self.id} @ {self.created_at:%Y-%m-%d %H:%M}"

class AuctionItem(models.Model):
    run         = models.ForeignKey(AuctionScrapeRun, on_delete=models.CASCADE, related_name="items")
    item_id     = models.BigIntegerField(db_index=True)          # auctionet id
    title       = models.CharField(max_length=500)
    url         = models.URLField()
    estimate    = models.IntegerField(null=True)
    info_text   = models.TextField(blank=True, default="")
    currency    = models.CharField(max_length=10, blank=True, default="")
    current_bid = models.FloatField(null=True, blank=True)
    ends_at     = models.CharField(null=True, blank=True)    # auction end
    location    = models.CharField(max_length=200, blank=True, default="")
    main_image_url = models.URLField()

    def __str__(self):
        return f"{self.item_id} — {self.title[:60]}"
