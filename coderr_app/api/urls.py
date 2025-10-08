from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileView, BusinessProfileView, CustomerProfileView, OfferDetailItemView, OrderListCreateView, OrderDetailView, OrderCountView, CompletedOrderCountView,  BaseInfoView, OfferViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r"offers", OfferViewSet, basename="offer")
router.register(r"reviews", ReviewViewSet, basename="review")


urlpatterns = [
    path("", include(router.urls)),
    path("profile/<int:pk>/", ProfileView.as_view(), name="profile-detail"),
    path('profiles/business/', BusinessProfileView.as_view(),
         name='business-profile-list'),
    path('profiles/customer/', CustomerProfileView.as_view(),
         name='customer-profile-list'),
    path("offerdetails/<int:id>/", OfferDetailItemView.as_view(),
         name="offer-detail-item"),
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:id>/", OrderDetailView.as_view(), name="order-detail"),
    path("order-count/<int:business_user_id>/",
         OrderCountView.as_view(), name="order-count"),
    path("completed-order-count/<int:business_user_id>/",
         CompletedOrderCountView.as_view(), name="completed-order-count"),
    path("base-info/", BaseInfoView.as_view(), name="base-info"),
]
