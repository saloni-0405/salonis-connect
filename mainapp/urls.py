from django.urls import path
from . import views

urlpatterns = [

    # HOME
    path('', views.home, name='home'),

    # AUTH
    path('customer-register/', views.customer_register, name='customer_register'),
    path('worker-register/', views.worker_register, name='worker_register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # SERVICES
    path('categories/', views.category_list, name='category_list'),
    path('workers/<int:category_id>/', views.worker_list, name='worker_list'),
    path('worker-profile/<int:worker_id>/', views.worker_profile, name='worker_profile'),
    path('search/', views.search_services, name='search_services'),

    # BOOKING
    path('book/<int:worker_id>/', views.book_worker, name='book_worker'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('add-review/<int:booking_id>/', views.add_review, name='add_review'),
    path('confirm-completion/<int:booking_id>/', views.confirm_completion, name='confirm_completion'),

    # CUSTOMER
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('join-as-customer/', views.join_as_customer, name='join_as_customer'),

    # WORKER
    path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('edit-profile/', views.edit_worker_profile, name='edit_worker_profile'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('accept-booking/<int:booking_id>/', views.accept_booking, name='accept_booking'),
    path('start-work/<int:booking_id>/', views.start_work, name='start_work'),
    path('complete-work/<int:booking_id>/', views.complete_work, name='complete_work'),

    # ADMIN
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-workers/', views.manage_workers, name='manage_workers'),
    path('toggle-verification/<int:worker_id>/', views.toggle_worker_verification, name='toggle_worker_verification'),

    # CONTACT
    path('contact-whatsapp/', views.whatsapp_contact, name='whatsapp_contact'),

    # API
    path('api/workers/', views.api_workers, name='api_workers'),
    path('api/reviews/', views.api_reviews, name='api_reviews'),
    path('api/worker/<int:worker_id>/', views.api_worker_detail, name='api_worker_detail'),
    path('api/book-service/', views.api_create_booking, name='api_create_booking'),
    path('api/workers-all/', views.api_workers_all, name='api_workers_all'),
]