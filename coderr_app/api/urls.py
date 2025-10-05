from django.contrib import admin
from django.urls import path, include
from .views import ProfileView, BusinessProfileView, CustomerProfileView, OfferListCreateView, OfferDetailView, OfferDetailItemView, OrderListCreateView, OrderDetailView, OrderCountView, CompletedOrderCountView, ReviewListCreateView, ReviewDetailView, BaseInfoView

urlpatterns = [
    path("profile/<int:pk>/", ProfileView.as_view(), name="profile-detail"),
    path('profiles/business/', BusinessProfileView.as_view(),
         name='business-profile-list'),
    path('profiles/customer/', CustomerProfileView.as_view(),
         name='customer-profile-list'),
    path("offers/", OfferListCreateView.as_view(), name="offer-list-create"),
    path("offers/<int:id>/", OfferDetailView.as_view(), name="offer-detail"),
    path("offerdetails/<int:id>/", OfferDetailItemView.as_view(),
         name="offer-detail-item"),
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:id>/", OrderDetailView.as_view(), name="order-detail"),
    path("order-count/<int:business_user_id>/",
         OrderCountView.as_view(), name="order-count"),
    path("completed-order-count/<int:business_user_id>/",
         CompletedOrderCountView.as_view(), name="completed-order-count"),
    path("reviews/", ReviewListCreateView.as_view(), name="review-list-create"),
    path("reviews/<int:id>/", ReviewDetailView.as_view(), name="review-detail"),
    path("base-info/", BaseInfoView.as_view(), name="base-info"),
]
