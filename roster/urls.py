from django.urls import path

from . import views

app_name = 'roster'

urlpatterns = [
    path('', views.OwnedCharacterListView.as_view(), name='owned-character-list'),
    path('characters/add/', views.OwnedCharacterCreateView.as_view(), name='owned-character-add'),
    path('characters/<int:pk>/', views.OwnedCharacterDetailView.as_view(), name='owned-character-detail'),
    path('characters/<int:pk>/edit/', views.OwnedCharacterUpdateView.as_view(), name='owned-character-edit'),
    path('characters/<int:pk>/talents/', views.TalentProgressCreateView.as_view(), name='talent-progress-add'),
    path('materials/', views.MaterialIndexView.as_view(), name='material-index'),
    path('materials/summary/', views.MaterialSummaryView.as_view(), name='material-summary'),
    path('recommendations/', views.RecommendationIndexView.as_view(), name='recommendations'),
]
