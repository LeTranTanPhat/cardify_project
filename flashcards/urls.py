from django.urls import path
from . import views

urlpatterns = [
    # ================= UI AUTH =================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ================= DASHBOARD =================
    path('', views.dashboard, name='dashboard'),
    path('history/', views.study_history, name='study_history'),
    path('api/save-session/', views.save_study_session, name='save_session'),
    path('community/', views.community_decks, name='community_decks'),
    
    # ================= PROFILE =================
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),

    # ================= DECK =================
    path('create-deck/', views.create_deck, name='create_deck'), 
    path('deck/<int:deck_id>/add-card/', views.add_card, name='add_card'),
    path('deck/<int:deck_id>/arena/', views.arena, name='arena'),
    path('deck/<int:deck_id>/edit/', views.edit_deck, name='edit_deck'),    
    path('deck/<int:deck_id>/delete/', views.delete_deck, name='delete_deck'),

    # ================= CARD =================
    path('card/<int:card_id>/edit/', views.edit_card, name='edit_card'),
    path('card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    path('deck/<int:deck_id>/ai-generate/', views.ai_generate_cards, name='ai_generate_cards'),
    path('deck/<int:deck_id>/ai-generate/', views.ai_generate_cards, name='ai_generate_cards'),

    # ================= GAME =================
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('add-heart/', views.add_heart, name='add_heart'),
    path('reduce-heart/', views.reduce_heart, name='reduce_heart'),
    path('api/add-xp/', views.api_add_xp, name='api_add_xp'),

    # ================= DICTIONARY =================
    path('dictionary/', views.dictionary_view, name='dictionary'),
    path('dictionary/all-vocab/', views.all_vocab_view, name='all_vocab'),
    path('dictionary/upload-csv/', views.upload_csv_view, name='upload_csv'),
    path('dictionary/delete-all/', views.delete_all_vocab, name='delete_all_vocab'),
    path('deck/<int:deck_id>/import/', views.import_cards_csv, name='import_cards'),

    # ================= API USER =================
    path('api/register/', views.api_register),
    path('api/login/', views.api_login),
    path('api/logout/', views.api_logout),
    path('api/profile/', views.api_profile),
    path('api/profile/update/', views.api_update_profile),
]