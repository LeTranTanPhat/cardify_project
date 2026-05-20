from django.urls import path
from . import views

urlpatterns = [
    # ================= UI AUTH =================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # ================= DASHBOARD & COMMUNITY =================
    path('', views.dashboard, name='dashboard'),
    path('community/', views.community_decks, name='community_decks'),
    path('api/community/', views.api_community_decks, name='api_community'), # API Cuộn vô hạn

    # ================= PROFILE =================
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # ================= DECK (BỘ THẺ) =================
    path('create-deck/', views.create_deck, name='create_deck'), 
    path('deck/<int:deck_id>/edit/', views.edit_deck, name='edit_deck'),    
    path('deck/<int:deck_id>/delete/', views.delete_deck, name='delete_deck'),
    path('deck/<int:deck_id>/import/', views.import_cards_csv, name='import_cards'),

    # ================= CARD (THẺ) =================
    path('deck/<int:deck_id>/add-card/', views.add_card, name='add_card'),
    path('card/<int:card_id>/edit/', views.edit_card, name='edit_card'),
    path('card/<int:card_id>/delete/', views.delete_card, name='delete_card'),
    path('deck/<int:deck_id>/bulk-delete/', views.bulk_delete_cards, name='bulk_delete_cards'),

    # ================= AI STUDIO (ĐÃ CẬP NHẬT LUỒNG MỚI) =================
    path('ai-studio/', views.global_ai_studio, name='global_ai_studio'),
    
    # API AI (Mới - Không cần truyền deck_id trên URL)
    path('api/ai/generate/topic/', views.ai_generate_topic_raw, name='ai_generate_topic_raw'),
    path('api/ai/generate/image/', views.ai_generate_image_raw, name='ai_generate_image_raw'),
    
    # API Lưu từng thẻ (Mới)
    path('api/cards/save-single/', views.save_single_card, name='save_single_card'),

    # (Đã xóa 2 url cũ là ai_generate_cards và ai_generate_topic vì không còn dùng nữa)

    # ================= GAME & STUDY =================
    path('deck/<int:deck_id>/arena/', views.arena, name='arena'),
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('history/', views.study_history, name='study_history'),
    path('api/save-session/', views.save_study_session, name='save_session'),
    path('add-heart/', views.add_heart, name='add_heart'),
    path('reduce-heart/', views.reduce_heart, name='reduce_heart'),
    path('api/add-xp/', views.api_add_xp, name='api_add_xp'),

    # ================= DICTIONARY =================
    path('dictionary/', views.dictionary_view, name='dictionary'),
    path('dictionary/all-vocab/', views.all_vocab_view, name='all_vocab'),
    path('dictionary/upload-csv/', views.upload_csv_view, name='upload_csv'),
    path('dictionary/delete-all/', views.delete_all_vocab, name='delete_all_vocab'),
    path('dictionary/bulk-delete/', views.bulk_delete_vocab, name='bulk_delete_vocab'),
    path('dictionary/delete/<int:vocab_id>/', views.delete_single_vocab, name='delete_single_vocab'),
    
    # ================= API USER =================
    path('api/register/', views.api_register),
    path('api/login/', views.api_login),
    path('api/logout/', views.api_logout),
    path('api/profile/', views.api_profile),
    path('api/profile/update/', views.api_update_profile),
]