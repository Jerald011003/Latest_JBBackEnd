from django.urls import path
from . import views
from .views import UserRegistrationView, csrf_token_view, UserLoginView, UserBalanceView, UserDetailsView, TransferView,\
    PasswordVerificationView, TransactionListView, NotificationListCreateView, NotificationDetailView, TopUpRequestCreateView, TopUpRequestDetailView, UpdateHeightWeightView, \
    CanteenListView, FoodCategoryListView, FoodListView, OrderCreateView, OrderListView, UpdateOrderPaymentStatusView, FeaturedFoodListView, UserVerificationView, TransferBuyerAndVendorView


urlpatterns = [
    path('home/', views.hello_world, name='hello_world'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('csrf/', csrf_token_view, name='csrf_token'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('balance/', UserBalanceView.as_view(), name='user-balance'),  # Added URL pattern for balance
    path('details/', UserDetailsView.as_view(), name='user-details'),
    path('transfer/', TransferView.as_view(), name='user-transfer'),
    path('transferbuyerandvendor/', TransferBuyerAndVendorView.as_view(), name='transfer_buyer_and_vendor'),
    path('verify-password/', PasswordVerificationView.as_view(), name='verify-password'),
    path('verify-user/', UserVerificationView.as_view(), name='verify-user'),
    path('transactions/', TransactionListView.as_view(), name='user-transactions'),
    path('notifications/', NotificationListCreateView.as_view(), name='notifications-list-create'),
    path('notifications/details/', NotificationDetailView.as_view(), name='notifications-detail'),
    path('top-up-requests/', TopUpRequestCreateView.as_view(), name='top-up-requests-list'),
    path('top-up-requests/<int:pk>/', TopUpRequestDetailView.as_view(), name='top-up-request-detail'),
    path('update-height-weight/', UpdateHeightWeightView.as_view(), name='update-height-weight'),

    path('canteens/', CanteenListView.as_view(), name='canteen-list'),
    path('canteens/<int:canteen_id>/categories/', FoodCategoryListView.as_view(), name='food-category-list'),
    path('categories/<int:category_id>/foods/', FoodListView.as_view(), name='food-list'),
    path('featured-foods/', FeaturedFoodListView.as_view(), name='featured-food-list'),
    path('create-order/', OrderCreateView.as_view(), name='order-create'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/pay/', UpdateOrderPaymentStatusView.as_view(), name='order-pay'),

]
