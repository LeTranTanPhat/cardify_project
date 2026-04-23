from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create-deck/', views.create_deck, name='create_deck'), 
    path('deck/<int:deck_id>/add-card/', views.add_card, name='add_card'),
    path('deck/<int:deck_id>/arena/', views.arena, name='arena'),
    path('deck/<int:deck_id>/edit/', views.edit_deck, name='edit_deck'),    
    path('deck/<int:deck_id>/delete/', views.delete_deck, name='delete_deck'),
    path('card/<int:card_id>/edit/', views.edit_card, name='edit_card'),
    path('card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('add-heart/', views.add_heart, name='add_heart'),
    path('reduce-heart/', views.reduce_heart, name='reduce_heart'),
    path('dictionary/', views.dictionary_view, name='dictionary'),
    path('dictionary/all-vocab/', views.all_vocab_view, name='all_vocab'),
    path('dictionary/upload-csv/', views.upload_csv_view, name='upload_csv'),
    path('dictionary/delete-all/', views.delete_all_vocab, name='delete_all_vocab'),
]