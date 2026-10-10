from django.urls import path

from . import views

app_name = 'vault'

urlpatterns = [
    path('', views.entry_list, name='list'),
    path('entries/new/', views.entry_create, name='create'),
    path('entries/<int:pk>/', views.entry_detail, name='detail'),
    path('entries/<int:pk>/edit/', views.entry_update, name='update'),
    path('entries/<int:pk>/delete/', views.entry_delete, name='delete'),
    path('entries/<int:pk>/reveal/', views.reveal_password, name='reveal_password'),
    path('entries/<int:pk>/copy/', views.copy_password, name='copy_password'),
    path('passwords/generate/', views.generated_password, name='generate_password'),
    path('tools/', views.tools, name='tools'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/json/', views.export_json, name='export_json'),
    path('import/csv/', views.import_csv_view, name='import_csv'),
    path('restore/json/', views.restore_json, name='restore_json'),
]
