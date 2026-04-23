import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse    
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Deck, Profile, Flashcard, DictionaryWord

# === 1. QUẢN LÝ TRANG CHỦ & BỘ THẺ ===

@login_required(login_url='/admin/login/')
def dashboard(request):
    # Lấy hồ sơ nhân vật (Energy, Level, XP)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Lấy danh sách các bộ thẻ của người dùng, sắp xếp mới nhất lên đầu
    decks = Deck.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'decks': decks,
        'profile': profile
    }
    return render(request, 'flashcards/dashboard.html', context)

@login_required(login_url='/admin/login/')
def create_deck(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        is_public = request.POST.get('is_public') == 'on' 
        
        Deck.objects.create(
            user=request.user,
            title=title,
            description=description,
            is_public=is_public
        )
        messages.success(request, "Đã tạo bộ thẻ mới thành công!")
        return redirect('dashboard')
        
    return render(request, 'flashcards/create_deck.html')

@login_required(login_url='/admin/login/')
def edit_deck(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    if request.method == 'POST':
        deck.title = request.POST.get('title')
        deck.description = request.POST.get('description')
        deck.is_public = request.POST.get('is_public') == 'on'
        deck.save()
        messages.success(request, "Đã cập nhật bộ thẻ.")
        return redirect('dashboard')
    return render(request, 'flashcards/edit_deck.html', {'deck': deck})

@login_required(login_url='/admin/login/')
def delete_deck(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    if request.method == 'POST':
        deck.delete()
        messages.info(request, "Đã xóa bộ thẻ.")
    return redirect('dashboard')

# === 2. QUẢN LÝ THẺ (FLASHCARDS) ===

@login_required(login_url='/admin/login/')
def add_card(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    if request.method == 'POST':
        front = request.POST.get('front_side')
        back = request.POST.get('back_side')
        Flashcard.objects.create(deck=deck, front_side=front, back_side=back)
        return redirect('add_card', deck_id=deck.id)
        
    cards = deck.cards.all().order_by('-id')
    return render(request, 'flashcards/add_card.html', {'deck': deck, 'cards': cards})

@login_required(login_url='/admin/login/')
def edit_card(request, card_id):
    card = get_object_or_404(Flashcard, id=card_id, deck__user=request.user)
    if request.method == 'POST':
        card.front_side = request.POST.get('front_side')
        card.back_side = request.POST.get('back_side')
        card.save()
        return redirect('add_card', deck_id=card.deck.id)
    return render(request, 'flashcards/edit_card.html', {'card': card})

@login_required(login_url='/admin/login/')
def delete_card(request, card_id):
    card = get_object_or_404(Flashcard, id=card_id, deck__user=request.user)
    deck_id = card.deck.id
    if request.method == 'POST':
        card.delete()
    return redirect('add_card', deck_id=deck_id)

# === 3. CHẾ ĐỘ HỌC & GAMIFICATION (ARENA/POMODORO) ===

@login_required(login_url='/admin/login/')
def arena(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Kiểm tra năng lượng trước khi vào đấu trường
    if profile.energy < 2:
        messages.warning(request, "Bạn không đủ năng lượng (cần 2⚡)! Hãy vào Trạm hồi máu để nạp lại.")
        return redirect('dashboard')
    
    cards = deck.cards.all()
    if not cards:
        messages.warning(request, "Bộ thẻ này chưa có nội dung để học!")
        return redirect('dashboard')
    
    # Thực hiện trừ 2 năng lượng và reset 5 tim khi bắt đầu ván đấu
    profile.energy -= 2
    profile.hearts = 5
    profile.save()
    
    return render(request, 'flashcards/arena.html', {'deck': deck, 'cards': cards, 'profile': profile})

@login_required(login_url='/admin/login/')
def pomodoro(request):
    return render(request, 'flashcards/pomodoro.html')

@csrf_exempt  
@login_required(login_url='/admin/login/')
def add_heart(request):
    """Hàm nạp Năng lượng (Thay thế hồi tim cũ). Gọi khi xong Pomodoro."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    # Hồi 20 năng lượng mỗi lần xong Pomodoro, tối đa 100
    if profile.energy < 100:
        profile.energy = min(profile.energy + 20, 100)
        profile.save()
    return JsonResponse({'energy': profile.energy, 'status': 'success'})

@csrf_exempt  
@login_required(login_url='/admin/login/')
def reduce_heart(request):
    """Hàm trừ tim (Khi trả lời sai trong Arena)."""
    if request.method == 'POST':
        profile, created = Profile.objects.get_or_create(user=request.user)
        if profile.hearts > 0:
            profile.hearts -= 1
            profile.save()
        return JsonResponse({'hearts': profile.hearts, 'status': 'success'})
    return JsonResponse({'error': 'Yêu cầu không hợp lệ'}, status=400)

# === 4. TỪ ĐIỂN & THƯ VIỆN TỔNG HỢP ===

def dictionary_view(request):
    return render(request, 'flashcards/dictionary.html')

def all_vocab_view(request):
    words = DictionaryWord.objects.all().values('language', 'word', 'meaning')
    formatted_words = []
    flag_map = {'en': '🇬🇧', 'zh': '🇨🇳', 'ko': '🇰🇷'}
    name_map = {'en': 'Tiếng Anh', 'zh': 'Tiếng Trung', 'ko': 'Tiếng Hàn'}
    
    for w in words:
        formatted_words.append({
            'lang': w['language'],
            'flag': flag_map.get(w['language'], '🌍'),
            'langName': name_map.get(w['language'], 'Khác'),
            'word': w['word'],
            'meaning': w['meaning']
        })
    
    context = {'db_words': json.dumps(formatted_words)}
    return render(request, 'flashcards/all_vocab.html', context)

def upload_csv_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        
        words_to_create = []
        for row in reader:
            word = row.get('Word', '').strip()
            meaning = row.get('Meaning', '').strip()
            language = row.get('Language', 'en').strip()
            if word and meaning:
                words_to_create.append(DictionaryWord(word=word, meaning=meaning, language=language))
        
        if words_to_create:
            DictionaryWord.objects.bulk_create(words_to_create)
            messages.success(request, f"Đã tải lên thành công {len(words_to_create)} từ vựng!")
            
    return redirect('all_vocab')

def delete_all_vocab(request):
    if request.method == 'POST':
        DictionaryWord.objects.all().delete()
        messages.success(request, "Đã dọn sạch thư viện từ vựng!")
    return redirect('all_vocab')