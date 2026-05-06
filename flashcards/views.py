import csv 
import json
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse    
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import Deck, Profile, Flashcard, DictionaryWord, CardProgress, StudySession
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.http import Http404
import google.generativeai as genai

# === 1. QUẢN LÝ TRANG CHỦ & BỘ THẺ ===

@login_required(login_url='/login/')
def dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
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

@login_required(login_url='/login/')
def community_decks(request):
    # Lấy TẤT CẢ bộ thẻ đang được public, nhưng (tùy chọn) loại trừ các thẻ do chính mình tạo
    # để tránh hiển thị lại những thẻ đã có ở Dashboard
    public_decks = Deck.objects.filter(is_public=True).exclude(user=request.user).order_by('-created_at')
    
    context = {
        'public_decks': public_decks
    }
    return render(request, 'flashcards/community.html', context)

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

# --- CẤU HÌNH AI ---
# Dán mã API Key đầy đủ của bạn vào đây (mã có trong ảnh Google AI Studio của bạn)
GEMINI_API_KEY = "AIzaSyDpMPP-Rd40Ykdx8SCS24bImWFLeHYQrEo" 
genai.configure(api_key=GEMINI_API_KEY)

@csrf_exempt
def ai_generate_cards(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    
    if request.method == 'POST':
        upload_file = request.FILES.get('file')
        if not upload_file:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy file!'})

        try:
            # 1. Khởi tạo Model Gemini 1.5 Flash (Nhanh và nhẹ)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')

            # 2. Đọc nội dung file gửi lên
            file_data = upload_file.read()
            file_mime_type = upload_file.content_type

            # 3. Câu lệnh "ép" AI trả về đúng định dạng JSON
            prompt = """
            Bạn là một trợ lý giáo dục. Hãy phân tích hình ảnh/tài liệu này và trích xuất các từ vựng hoặc khái niệm quan trọng.
            YÊU CẦU BẮT BUỘC: Trả về kết quả dưới dạng JSON Array (Mảng).
            Mỗi phần tử có cấu trúc: {"front": "Từ vựng/Câu hỏi", "back": "Nghĩa/Câu trả lời tiếng Việt"}
            Chỉ trả về mã JSON, không nói thêm gì khác.
            """

            # 4. Gửi file lên AI
            response = model.generate_content([
                prompt,
                {'mime_type': file_mime_type, 'data': file_data}
            ])

            # 5. Xử lý chuỗi JSON từ AI (loại bỏ các ký tự thừa như ```json ...)
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            data_list = json.loads(raw_text)

            # 6. Lưu hàng loạt vào Database
            new_cards = []
            for item in data_list:
                front = item.get('front', '').strip()
                back = item.get('back', '').strip()
                if front and back:
                    new_cards.append(Flashcard(deck=deck, front_side=front, back_side=back))
            
            if new_cards:
                Flashcard.objects.bulk_create(new_cards)
                return JsonResponse({
                    'status': 'success', 
                    'message': f'Thành công! AI đã tạo {len(new_cards)} thẻ từ ảnh của bạn.'
                })
            
            return JsonResponse({'status': 'error', 'message': 'AI không tìm thấy nội dung phù hợp.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Lỗi AI: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Method không hợp lệ'}, status=400)

# ---> ĐÃ THÊM HÀM IMPORT HÀNG LOẠT VÀO ĐÂY <---
@login_required(login_url='/login/')
def import_cards_csv(request, deck_id):
    # Bảo mật: Đảm bảo chỉ user chủ bộ thẻ mới có quyền import
    deck = get_object_or_404(Deck, id=deck_id, user=request.user)
    
    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            messages.error(request, 'Vui lòng chọn một file để tải lên!')
            return redirect('add_card', deck_id=deck.id)
            
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Chỉ hỗ trợ file định dạng .csv!')
            return redirect('add_card', deck_id=deck.id)

        try:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.reader(decoded_file)
            
            new_cards = []
            for row in reader:
                if len(row) >= 2:
                    front = row[0].strip()
                    back = row[1].strip()
                    if front and back:
                        new_cards.append(Flashcard(deck=deck, front_side=front, back_side=back))
            
            if new_cards:
                Flashcard.objects.bulk_create(new_cards)
                messages.success(request, f'Tuyệt vời! Đã import thành công {len(new_cards)} thẻ mới.')
            else:
                messages.warning(request, 'Không tìm thấy dữ liệu hợp lệ trong file (Yêu cầu Cột 1: Mặt trước, Cột 2: Mặt sau).')
                
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra khi đọc file: {str(e)}')
            
    return redirect('add_card', deck_id=deck.id)
# ------------------------------------------------

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
    # 1. Bỏ điều kiện user=request.user để có thể tìm được cả bộ thẻ của người khác
    deck = get_object_or_404(Deck, id=deck_id)
    
    # 2. Kiểm tra xem user có quyền học bộ thẻ này không
    # (Nếu không phải chủ bộ thẻ VÀ bộ thẻ đang khóa private thì không cho vào)
    if deck.user != request.user and not deck.is_public:
        raise Http404("Bộ thẻ này đang ở chế độ riêng tư hoặc không tồn tại.")

    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if profile.energy < 2:
        messages.warning(request, "Bạn không đủ năng lượng (cần 2⚡)! Hãy vào Trạm hồi năng lượng để nạp lại.")
        return redirect('dashboard')
    
    cards = deck.cards.all()
    if not cards:
        messages.warning(request, "Bộ thẻ này chưa có nội dung để học!")
        return redirect('dashboard')
    
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
    profile, created = Profile.objects.get_or_create(user=request.user)
    if profile.energy < 100:
        profile.energy = min(profile.energy + 20, 100)
        profile.save()
    return JsonResponse({'energy': profile.energy, 'status': 'success'})

@csrf_exempt  
@login_required(login_url='/login/')
def reduce_heart(request):
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
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Định dạng không hợp lệ! Vui lòng tải lên file .csv, .xlsx hoặc .xls")
                return redirect('all_vocab')

            df = df.fillna('')
            words_to_create = []
            
            for index, row in df.iterrows():
                word = str(row.get('Word', '')).strip()
                meaning = str(row.get('Meaning', '')).strip()
                language = str(row.get('Language', 'en')).strip()
                
                if word and meaning:
                    words_to_create.append(DictionaryWord(word=word, meaning=meaning, language=language))
            
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
# API ĐĂNG KÝ, ĐĂNG NHẬP, ĐĂNG XUẤT, PROFILE
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

@login_required
def api_logout(request):
    logout(request)
    return JsonResponse({'message': 'Đăng xuất thành công'})

@login_required
def api_profile(request):
    profile = request.user.profile
    return JsonResponse({
        'username': request.user.username,
        'energy': profile.energy,
        'hearts': profile.hearts,
        'level': profile.level
    })

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
# GIAO DIỆN AUTH
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
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username or not password or not confirm_password:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin bắt buộc.")
            return redirect('register')
        if password != confirm_password:
            messages.error(request, "Mật khẩu và Xác nhận mật khẩu không khớp!")
            return redirect('register')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác!")
            return redirect('register')
        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email này đã được sử dụng!")
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            Profile.objects.create(user=user)
            messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Đã xảy ra lỗi: {str(e)}")
            return redirect('register')
    return render(request, 'auth/register.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'auth/profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        old_pwd = request.POST.get('old_password')
        new_pwd = request.POST.get('new_password')
        confirm_pwd = request.POST.get('confirm_password')

        if not request.user.check_password(old_pwd):
            messages.error(request, "Mật khẩu hiện tại không chính xác.")
            return redirect('profile')
        if new_pwd != confirm_pwd:
            messages.error(request, "Mật khẩu mới không khớp nhau.")
            return redirect('profile')
        if len(new_pwd) < 6:
            messages.error(request, "Mật khẩu mới phải có ít nhất 6 ký tự.")
            return redirect('profile')

        request.user.set_password(new_pwd)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Đổi mật khẩu thành công!")
        return redirect('profile')
    return redirect('profile')

# ============ XP & LỊCH SỬ HỌC =================== 

@csrf_exempt
@login_required
def api_add_xp(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method không hợp lệ'}, status=400)
    try:
        data = json.loads(request.body)
        xp_earned = int(data.get('xp', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Dữ liệu không hợp lệ'}, status=400)

    if xp_earned <= 0:
        return JsonResponse({'error': 'Số XP phải lớn hơn 0'}, status=400)

    profile = request.user.profile
    profile.xp += xp_earned
    
    level_up = False
    xp_needed_for_next_level = profile.level * 100 

    while profile.xp >= xp_needed_for_next_level:
        profile.xp -= xp_needed_for_next_level
        profile.level += 1
        level_up = True
        profile.energy = 100
        profile.hearts = 5
        xp_needed_for_next_level = profile.level * 100 

    profile.save()

    return JsonResponse({
        'success': True,
        'level_up': level_up,
        'current_level': profile.level,
        'current_xp': profile.xp,
        'xp_needed': xp_needed_for_next_level,
        'energy': profile.energy,
        'hearts': profile.hearts,
        'message': f'Bạn được cộng {xp_earned} XP!'
    }, status=200)
    
@csrf_exempt
@login_required
def record_card_interaction(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        card_id = data.get('card_id')
        is_remembered = data.get('is_remembered')
        
        # Đã fix lỗi đổi Card -> Flashcard
        card = get_object_or_404(Flashcard, id=card_id)
        progress, created = CardProgress.objects.get_or_create(user=request.user, card=card)
        
        if is_remembered:
            progress.box_number = min(progress.box_number + 1, 5)
            if progress.box_number == 5:
                progress.is_mastered = True
        else:
            progress.box_number = max(progress.box_number - 1, 1)
            progress.is_mastered = False
            
        progress.save()
        return JsonResponse({'status': 'success', 'box_number': progress.box_number})

@login_required
def study_history(request):
    sessions = StudySession.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'flashcards/study_history.html', {'sessions': sessions})

# Hàm quan trọng nhất vừa được thêm để chốt lịch sử:
@csrf_exempt
@login_required
def save_study_session(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            deck_id = data.get('deck_id')
            cards_reviewed = data.get('cards_reviewed', 0)
            correct_answers = data.get('correct_answers', 0)
            xp_gained = data.get('xp_gained', 0)

            deck = get_object_or_404(Deck, id=deck_id)
            
            StudySession.objects.create(
                user=request.user,
                deck=deck,
                cards_reviewed=cards_reviewed,
                correct_answers=correct_answers,
                xp_gained=xp_gained
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'})