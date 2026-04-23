import json
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse    
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Deck, Profile, Flashcard, DictionaryWord
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

# === 1. QUẢN LÝ TRANG CHỦ & BỘ THẺ ===

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def delete_deck(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    if request.method == 'POST':
        deck.delete()
        messages.info(request, "Đã xóa bộ thẻ.")
    return redirect('dashboard')

# === 2. QUẢN LÝ THẺ (FLASHCARDS) ===

@login_required(login_url='/login/')
def add_card(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    if request.method == 'POST':
        front = request.POST.get('front_side')
        back = request.POST.get('back_side')
        Flashcard.objects.create(deck=deck, front_side=front, back_side=back)
        return redirect('add_card', deck_id=deck.id)
        
    cards = deck.cards.all().order_by('-id')
    return render(request, 'flashcards/add_card.html', {'deck': deck, 'cards': cards})

@login_required(login_url='/login/')
def edit_card(request, card_id):
    card = get_object_or_404(Flashcard, id=card_id, deck__user=request.user)
    if request.method == 'POST':
        card.front_side = request.POST.get('front_side')
        card.back_side = request.POST.get('back_side')
        card.save()
        return redirect('add_card', deck_id=card.deck.id)
    return render(request, 'flashcards/edit_card.html', {'card': card})

@login_required(login_url='/login/')
def delete_card(request, card_id):
    card = get_object_or_404(Flashcard, id=card_id, deck__user=request.user)
    deck_id = card.deck.id
    if request.method == 'POST':
        card.delete()
    return redirect('add_card', deck_id=deck_id)

# === 3. CHẾ ĐỘ HỌC & GAMIFICATION (ARENA/POMODORO) ===

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def pomodoro(request):
    return render(request, 'flashcards/pomodoro.html')

@csrf_exempt  
@login_required(login_url='/login/')
def add_heart(request):
    """Hàm nạp Năng lượng (Thay thế hồi tim cũ). Gọi khi xong Pomodoro."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    # Hồi 20 năng lượng mỗi lần xong Pomodoro, tối đa 100
    if profile.energy < 100:
        profile.energy = min(profile.energy + 20, 100)
        profile.save()
    return JsonResponse({'energy': profile.energy, 'status': 'success'})

@csrf_exempt  
@login_required(login_url='/login/')
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
        uploaded_file = request.FILES['csv_file']
        file_name = uploaded_file.name.lower()
        
        try:
            # 1. Đọc file dựa trên đuôi mở rộng
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Định dạng không hợp lệ! Vui lòng tải lên file .csv, .xlsx hoặc .xls")
                return redirect('all_vocab')

            # 2. Xử lý dữ liệu (Điền chuỗi rỗng vào các ô trống để tránh lỗi)
            df = df.fillna('')
            
            words_to_create = []
            for index, row in df.iterrows():
                # Lấy dữ liệu an toàn bằng .get() để tránh lỗi nếu thiếu cột
                word = str(row.get('Word', '')).strip()
                meaning = str(row.get('Meaning', '')).strip()
                language = str(row.get('Language', 'en')).strip()
                
                # Chỉ tạo từ vựng nếu cột Word và Meaning có nội dung
                if word and meaning:
                    words_to_create.append(DictionaryWord(word=word, meaning=meaning, language=language))
            
            # 3. Lưu vào Database
            if words_to_create:
                DictionaryWord.objects.bulk_create(words_to_create)
                messages.success(request, f"🎉 Đã tải lên thành công {len(words_to_create)} từ vựng!")
            else:
                messages.warning(request, "File không có dữ liệu hoặc sai tên cột (Cần có cột 'Word' và 'Meaning').")
                
        except Exception as e:
            messages.error(request, f"Đã xảy ra lỗi khi đọc file: {str(e)}")
            
    return redirect('all_vocab')

def delete_all_vocab(request):
    if request.method == 'POST':
        DictionaryWord.objects.all().delete()
        messages.success(request, "Đã dọn sạch thư viện từ vựng!")
    return redirect('all_vocab')

# ===============================
# API ĐĂNG KÝ
# ===============================
@csrf_exempt
def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method không hợp lệ'}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'JSON không hợp lệ'}, status=400)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return JsonResponse({'error': 'Thiếu username hoặc password'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username đã tồn tại'}, status=400)

    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(user=user)

    return JsonResponse({'message': 'Đăng ký thành công'}, status=201)


# ===============================
# API ĐĂNG NHẬP
# ===============================
@csrf_exempt
def api_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method không hợp lệ'}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'JSON không hợp lệ'}, status=400)

    username = data.get('username')
    password = data.get('password')

    user = authenticate(request, username=username, password=password)

    if user:
        login(request, user)
        return JsonResponse({'message': 'Đăng nhập thành công'})
    else:
        return JsonResponse({'error': 'Sai tài khoản hoặc mật khẩu'}, status=400)


# ===============================
# API ĐĂNG XUẤT
# ===============================
@login_required
def api_logout(request):
    logout(request)
    return JsonResponse({'message': 'Đăng xuất thành công'})


# ===============================
# API PROFILE
# ===============================
@login_required
def api_profile(request):
    profile = request.user.profile

    return JsonResponse({
        'username': request.user.username,
        'energy': profile.energy,
        'hearts': profile.hearts,
        'level': profile.level
    })


# ===============================
# UPDATE PROFILE
# ===============================
@csrf_exempt
@login_required
def api_update_profile(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method không hợp lệ'}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({'error': 'JSON không hợp lệ'}, status=400)

    profile = request.user.profile

    profile.energy = data.get('energy', profile.energy)
    profile.hearts = data.get('hearts', profile.hearts)
    profile.save()

    return JsonResponse({'message': 'Cập nhật thành công'})

# ===============================
# LOGIN / REGISTER UI
# ===============================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Sai tài khoản hoặc mật khẩu")

    return render(request, 'auth/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username đã tồn tại")
            return redirect('register')

        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user)

        messages.success(request, "Đăng ký thành công!")
        return redirect('login')

    return render(request, 'auth/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')

