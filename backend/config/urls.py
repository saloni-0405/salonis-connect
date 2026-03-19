from django.contrib import admin
from django.urls import path
from mainapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('categories/', views.category_list, name='category_list'),

    path('workers/<int:category_id>/', views.worker_list, name='worker_list'),

    path('worker-profile/<int:worker_id>/', views.worker_profile, name='worker_profile'),

    path('book/<int:worker_id>/', views.book_worker, name='book_worker'),

    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('customer-register/', views.customer_register, name='customer_register'),
    path('worker-register/', views.worker_register, name='worker_register'),

    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)