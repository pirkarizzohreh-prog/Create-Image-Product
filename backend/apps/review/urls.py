from rest_framework.routers import DefaultRouter

from .views import ReviewItemViewSet

router = DefaultRouter()
router.register("review", ReviewItemViewSet, basename="review")

urlpatterns = router.urls
