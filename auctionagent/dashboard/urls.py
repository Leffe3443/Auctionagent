from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings

urlpatterns = [

    path("", views.return_dashboard, name="dashboard"),
    path("adminndata/", views.return_datanadmin, name="adminndata"),
    
    
    # API calls
    path("api/auction-agent/run-auctionsearch/", views.run_auction_agent, name="run_auction_agent"),
    path("api/auction-agent/ai/", views.ai_auction_agent, name="ai_auction_agent"),
    path("api/auction-agent/aifreesearch/", views.aifreesarch_auction_agent, name="ai_freesearch"),
    path("api/auction-agent/stats", views.auction_stats, name="auction_stats"),

    path("logout/", auth_views.LogoutView.as_view(next_page=settings.LOGIN_URL), name="logout"),

]