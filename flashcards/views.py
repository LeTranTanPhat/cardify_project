# -*- coding: utf-8 -*-
import csv
import json
import base64
import pandas as pd
import os

# --- Django Imports ---
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.core.paginator import Paginator

# --- Local Model Imports ---
from .models import Deck, Profile, Flashcard, DictionaryWord, CardProgress, StudySession

# ==========================================
# 1. AUTHENTICATION & PROFILE VIEWS (GIAO DIỆN)
# ==========================================

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


# ==========================================
# 2. AUTHENTICATION & PROFILE API (AJAX)
# ==========================================

@csrf_exempt
def api_register(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method không hợp lệ'}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
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
    except json.JSONDecodeError:
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
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON không hợp lệ'}, status=400)
        
    profile = request.user.profile
    profile.energy = data.get('energy', profile.energy)
    profile.hearts = data.get('hearts', profile.hearts)
    profile.save()
    return JsonResponse({'message': 'Cập nhật thành công'})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # Xử lý lưu dữ liệu người dùng gửi lên tại đây
        # Ví dụ: request.user.first_name = request.POST.get('first_name')
        # request.user.save()
        
        # Sau khi lưu thành công thì chuyển hướng về trang Profile
        return redirect('profile') 
        
    # Nếu là GET request, hiển thị trang form
    return render(request, 'auth/edit_profile.html')


# ==========================================
# 3. QUẢN LÝ TRANG CHỦ & BỘ THẺ (DECKS)
# ==========================================

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
def bulk_delete_cards(request, deck_id):
    if request.method == 'POST':
        # 1. Lấy bộ thẻ và bắt buộc phải thuộc sở hữu của người dùng đang đăng nhập
        deck = get_object_or_404(Deck, id=deck_id, user=request.user)
        
        # 2. Lấy danh sách các ID thẻ được chọn từ checkbox (name="card_ids")
        card_ids = request.POST.getlist('card_ids')
        
        if card_ids:
            # 3. ĐÃ SỬA: Đổi từ 'Card' thành 'Flashcard' cho đúng với Model định nghĩa ở trên
            # Lọc thêm deck=deck để đảm bảo an toàn tuyệt đối, không bị xóa nhầm thẻ của bộ khác
            deleted_count, _ = Flashcard.objects.filter(id__in=card_ids, deck=deck).delete()
            
            # Gửi thông báo thành công hiển thị số lượng thẻ thực tế đã bị xóa
            messages.success(request, f'Đã xóa thành công {deleted_count} thẻ ra khỏi bộ từ vựng!')
        else:
            messages.warning(request, 'Bạn chưa chọn thẻ nào để tiến hành xóa.')
            
    # Chuyển hướng quay trở lại đúng trang thêm/quản lý thẻ hiện tại
    return redirect('add_card', deck_id=deck_id)

# ==========================================
# 4. QUẢN LÝ THẺ (FLASHCARDS)
# ==========================================

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

@login_required(login_url='/login/')
def import_cards_csv(request, deck_id):
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
            
            # 1. Lấy danh sách các mặt trước đã tồn tại trong bộ thẻ này (Dùng set để tra cứu siêu nhanh)
            existing_fronts = set(Flashcard.objects.filter(deck=deck).values_list('front_side', flat=True))
            skipped_count = 0 # Bộ đếm số thẻ bị bỏ qua do trùng
            
            new_cards = []
            for row in reader:
                if len(row) >= 2:
                    front = row[0].strip()
                    back = row[1].strip()
                    if front and back:
                        # 2. Nếu mặt trước đã tồn tại, tăng biến đếm và bỏ qua dòng này
                        if front in existing_fronts:
                            skipped_count += 1
                            continue
                        
                        # Nếu là từ mới, thêm vào danh sách chờ và cập nhật luôn vào set để chống trùng nếu file CSV có các dòng giống nhau
                        new_cards.append(Flashcard(deck=deck, front_side=front, back_side=back))
                        existing_fronts.add(front)
            
            # 3. Tiến hành lưu và thông báo kết quả dựa trên số lượng thẻ mới lọc được
            if new_cards:
                Flashcard.objects.bulk_create(new_cards)
                success_msg = f'Tuyệt vời! Đã import thành công {len(new_cards)} thẻ mới.'
                if skipped_count > 0:
                    success_msg += f' (Đã tự động loại bỏ {skipped_count} từ bị trùng).'
                messages.success(request, success_msg)
            else:
                if skipped_count > 0:
                    messages.warning(request, f'Không có thẻ mới nào được thêm. Toàn bộ {skipped_count} từ trong file đều đã tồn tại trong bộ thẻ!')
                else:
                    messages.warning(request, 'Không tìm thấy dữ liệu hợp lệ trong file (Yêu cầu Cột 1: Mặt trước, Cột 2: Mặt sau).')
                
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra khi đọc file: {str(e)}')
            
    return redirect('add_card', deck_id=deck.id)


@login_required(login_url='/login/')
def global_ai_studio(request):
    user_decks = Deck.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'flashcards/ai_studio.html', {'user_decks': user_decks})


@csrf_exempt
@login_required(login_url='/login/')
def ai_generate_topic_raw(request):
    """
    Trả về dữ liệu JSON thẻ (mock) cho UI hiển thị thay vì lưu thẳng vào DB.
    ĐÃ SỬA: Đọc biến 'language' để trả về đúng ngôn ngữ người dùng yêu cầu.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic', '').strip().lower()
            language = data.get('language', 'en') # LẤY NGÔN NGỮ TỪ FRONTEND
            
            if not topic:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập chủ đề!'})

            mock_data = []

            # --- CHỦ ĐỀ 1: ĐỘNG VẬT ---
            if 'động vật' in topic or 'dong vat' in topic or 'animal' in topic:
                if language == 'en':
                    mock_data = [
                        {"front": "Dog", "back": "Con Chó"},
                        {"front": "Cat", "back": "Con Mèo"},
                        {"front": "Lion", "back": "Sư Tử"}
                    ]
                elif language == 'zh':
                    mock_data = [
                        {"front": "狗 (Gǒu)", "back": "Con Chó"},
                        {"front": "猫 (Māo)", "back": "Con Mèo"},
                        {"front": "狮子 (Shīzi)", "back": "Sư Tử"}
                    ]
                elif language == 'ko':
                    mock_data = [
                        {"front": "개 (Gae)", "back": "Con Chó"},
                        {"front": "고양이 (Goyang-i)", "back": "Con Mèo"},
                        {"front": "사자 (Saja)", "back": "Sư Tử"}
                    ]

            # --- CHỦ ĐỀ 2: TRÁI CÂY ---
            elif 'trái cây' in topic or 'trai cay' in topic or 'hoa quả' in topic or 'fruit' in topic:
                if language == 'en':
                    mock_data = [
                        {"front": "Apple", "back": "Quả Táo"},
                        {"front": "Banana", "back": "Quả Chuối"},
                        {"front": "Orange", "back": "Quả Cam"}
                    ]
                elif language == 'zh':
                    mock_data = [
                        {"front": "苹果 (Píngguǒ)", "back": "Quả Táo"},
                        {"front": "香蕉 (Xiāngjiāo)", "back": "Quả Chuối"},
                        {"front": "橙子 (Chéngzi)", "back": "Quả Cam"}
                    ]
                elif language == 'ko':
                    mock_data = [
                        {"front": "사과 (Sagwa)", "back": "Quả Táo"},
                        {"front": "바나나 (Banana)", "back": "Quả Chuối"},
                        {"front": "오렌지 (Orenji)", "back": "Quả Cam"}
                    ]

            # --- CHỦ ĐỀ 3: MÀU SẮC ---
            elif 'màu sắc' in topic or 'mau sac' in topic or 'color' in topic:
                if language == 'en':
                    mock_data = [
                        {"front": "Red", "back": "Màu Đỏ"},
                        {"front": "Blue", "back": "Màu Xanh Dương"},
                        {"front": "Green", "back": "Màu Xanh Lá"}
                    ]
                elif language == 'zh':
                    mock_data = [
                        {"front": "红色 (Hóngsè)", "back": "Màu Đỏ"},
                        {"front": "蓝色 (Lánsè)", "back": "Màu Xanh Dương"},
                        {"front": "绿色 (Lǜsè)", "back": "Màu Xanh Lá"}
                    ]
                elif language == 'ko':
                    mock_data = [
                        {"front": "빨간색 (Ppalgansaek)", "back": "Màu Đỏ"},
                        {"front": "파란색 (Paransaek)", "back": "Màu Xanh Dương"},
                        {"front": "초록색 (Choroksaek)", "back": "Màu Xanh Lá"}
                    ]

            # --- CHỦ ĐỀ 4: GIA ĐÌNH ---
            elif 'gia đình' in topic or 'gia dinh' in topic or 'family' in topic:
                if language == 'en':
                    mock_data = [
                        {"front": "Father", "back": "Bố / Cha"},
                        {"front": "Mother", "back": "Mẹ"},
                        {"front": "Older Brother", "back": "Anh Trai"}
                    ]
                elif language == 'zh':
                    mock_data = [
                        {"front": "爸爸 (Bàba)", "back": "Bố / Cha"},
                        {"front": "妈妈 (Māma)", "back": "Mẹ"},
                        {"front": "哥哥 (Gēge)", "back": "Anh Trai"}
                    ]
                elif language == 'ko':
                    mock_data = [
                        {"front": "아버지 (Abeoji)", "back": "Bố / Cha"},
                        {"front": "어머니 (Eomeoni)", "back": "Mẹ"},
                        {"front": "형 (Hyeong)", "back": "Anh Trai"}
                    ]

            # --- CHỦ ĐỀ 5: THỜI TIẾT ---
            elif 'thời tiết' in topic or 'thoi tiet' in topic or 'weather' in topic:
                if language == 'en':
                    mock_data = [
                        {"front": "Sunny", "back": "Trời Nắng"},
                        {"front": "Rainy", "back": "Trời Mưa"},
                        {"front": "Windy", "back": "Có Gió"}
                    ]
                elif language == 'zh':
                    mock_data = [
                        {"front": "晴天 (Qíngtiān)", "back": "Trời Nắng"},
                        {"front": "下雨 (Xiàyǔ)", "back": "Trời Mưa"},
                        {"front": "刮风 (Guāfēng)", "back": "Có Gió"}
                    ]
                elif language == 'ko':
                    mock_data = [
                        {"front": "맑음 (Malgeum)", "back": "Trời Nắng"},
                        {"front": "비 (Bi)", "back": "Trời Mưa"},
                        {"front": "바람 (Baram)", "back": "Có Gió"}
                    ]
            
            else:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Bản Demo hiện tại chỉ hỗ trợ: Động vật, Trái cây, Màu sắc, Gia đình, Thời tiết.'
                })

            return JsonResponse({'status': 'success', 'cards': mock_data})
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Lỗi hệ thống: {str(e)}'})
            
    return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'}, status=400)


@csrf_exempt
@login_required(login_url='/login/')
def ai_generate_image_raw(request):
    """
    Nhận file ảnh và trả về danh sách thẻ theo ngôn ngữ.
    """
    if request.method == 'POST':
        try:
            upload_file = request.FILES.get('file')
            # VỚI FORM DATA (Ảnh), dữ liệu text nằm trong request.POST
            language = request.POST.get('language', 'en') 
            
            if not upload_file:
                return JsonResponse({'status': 'error', 'message': 'Không tìm thấy file!'})
                
            mock_data = []
            if language == 'en':
                mock_data = [{"front": "Horse", "back": "Con Ngựa"}]
            elif language == 'zh':
                mock_data = [{"front": "马 (Mǎ)", "back": "Con Ngựa"}]
            elif language == 'ko':
                mock_data = [{"front": "말 (Mal)", "back": "Con Ngựa"}]
                
            return JsonResponse({'status': 'success', 'cards': mock_data})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Lỗi: {str(e)}'})
            
    return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'}, status=400)


@csrf_exempt
@login_required(login_url='/login/')
def save_single_card(request):
    """
    API để user lưu từng thẻ sau khi đã xem trước và chỉnh sửa trên UI.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            deck_id = data.get('deck_id')
            front = data.get('front')
            back = data.get('back')
            # Lấy thêm language nếu Model Flashcard của bạn có trường ngôn ngữ
            # language = data.get('language') 
            
            if not deck_id or not front or not back:
                return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ!'})

            deck = get_object_or_404(Deck, id=deck_id, user=request.user)
            
            # Nếu model của bạn cần truyền ngôn ngữ, hãy thêm vào đây: language=language
            Flashcard.objects.create(deck=deck, front_side=front, back_side=back)
            
            return JsonResponse({'status': 'success', 'message': 'Đã lưu thẻ!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'}, status=400)


# ==========================================
# 6. HỌC TẬP & GAMIFICATION (ARENA/POMODORO)
# ==========================================

@login_required(login_url='/login/')
def arena(request, deck_id):
    deck = get_object_or_404(Deck, id=deck_id)
    
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


# ==========================================
# 7. TỪ ĐIỂN & THƯ VIỆN TỔNG HỢP
# ==========================================
# Đảm bảo bạn đã import đúng Model DictionaryWord và pandas (pd) ở đầu file

def dictionary_view(request):
    return render(request, 'flashcards/dictionary.html')


def all_vocab_view(request):
    # SỬA LỖI 1: Bổ sung 'id' vào câu lệnh query values
    words = DictionaryWord.objects.all().values('id', 'language', 'word', 'meaning')
    formatted_words = []
    flag_map = {'en': '🇬🇧', 'zh': '🇨🇳', 'ko': '🇰🇷'}
    name_map = {'en': 'Tiếng Anh', 'zh': 'Tiếng Trung', 'ko': 'Tiếng Hàn'}
    
    for w in words:
        formatted_words.append({
            'id': w['id'], # <-- Đã có ID cung cấp cho JavaScript render
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
            # Đọc file dựa trên định dạng bằng pandas
            if file_name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
            else:
                messages.error(request, "Định dạng không hợp lệ! Vui lòng tải lên file .csv, .xlsx hoặc .xls")
                return redirect('all_vocab')

            df = df.fillna('')
            
            # 1. Lấy toàn bộ từ vựng đã có trong Từ điển đưa vào Set để check trùng cực nhanh
            existing_words = set(DictionaryWord.objects.values_list('word', flat=True))
            
            words_to_create = []
            skipped_count = 0  # Bộ đếm số từ bị trùng
            
            # 2. Duyệt qua từng dòng dữ liệu bằng pandas
            for index, row in df.iterrows():
                word = str(row.get('Word', '')).strip()
                meaning = str(row.get('Meaning', '')).strip()
                language = str(row.get('Language', 'en')).strip()
                
                if word and meaning:
                    # 3. KIỂM TRA TRÙNG LẶP: Nếu từ này đã tồn tại trong DB hoặc đã xử lý ở dòng trên
                    if word in existing_words:
                        skipped_count += 1
                        continue # Bỏ qua dòng này
                    
                    # Nếu là từ mới hoàn toàn
                    words_to_create.append(DictionaryWord(word=word, meaning=meaning, language=language))
                    
                    # Thêm ngay từ này vào set để nếu dòng dưới có bị lặp lại thì sẽ bị phát hiện ngay
                    existing_words.add(word)
            
            # 4. Lưu và đưa ra thông báo thông minh cho người dùng
            if words_to_create:
                DictionaryWord.objects.bulk_create(words_to_create)
                success_msg = f"🎉 Đã tải lên thành công {len(words_to_create)} từ vựng mới!"
                if skipped_count > 0:
                    success_msg += f" (Đã tự động loại bỏ {skipped_count} từ bị trùng)."
                messages.success(request, success_msg)
            else:
                if skipped_count > 0:
                    messages.warning(request, f"Không có từ mới nào được thêm. Toàn bộ {skipped_count} từ trong file đều đã tồn tại trong từ điển!")
                else:
                    messages.warning(request, "File không có dữ liệu hoặc sai tên cột (Cần có cột 'Word' và 'Meaning').")
                
        except Exception as e:
            messages.error(request, f"Đã xảy ra lỗi khi đọc file: {str(e)}")
            
    return redirect('all_vocab')


# BỔ SUNG: Hàm xóa đơn lẻ một từ vựng giải quyết dứt điểm lỗi 404
def delete_single_vocab(request, vocab_id):
    if request.method == 'POST':
        word_obj = get_object_or_404(DictionaryWord, id=vocab_id)
        word_text = word_obj.word
        word_obj.delete()
        messages.success(request, f"Đã xóa từ '{word_text}' thành công!")
    return redirect('all_vocab')


def delete_all_vocab(request):
    if request.method == 'POST':
        DictionaryWord.objects.all().delete()
        messages.success(request, "Đã dọn sạch thư viện từ vựng!")
    return redirect('all_vocab')


def bulk_delete_vocab(request):
    if request.method == 'POST':
        vocab_ids = request.POST.getlist('vocab_ids')
        # SỬA LỖI 2: Đổi từ Vocabulary sang đúng Model DictionaryWord
        deleted_count = DictionaryWord.objects.filter(id__in=vocab_ids).delete()[0]
        if deleted_count > 0:
            messages.success(request, f"Đã xóa hàng loạt {deleted_count} từ vựng đã chọn!")
        else:
            messages.warning(request, "Không có từ vựng nào được chọn để xóa.")
    return redirect('all_vocab') # Quay lại danh sách thư viện thay vì trang dashboard chung

# ==========================================
# 8. THƯ VIỆN CỘNG ĐỒNG (COMMUNITY)
# ==========================================

@login_required(login_url='/login/')
def community_decks(request):
    return render(request, 'flashcards/community.html')

def api_community_decks(request):
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', '-created_at')
    page_number = int(request.GET.get('page', 1))

    decks = Deck.objects.filter(is_public=True)
    if request.user.is_authenticated:
        decks = decks.exclude(user=request.user)

    if query:
        decks = decks.filter(title__icontains=query)

    if sort_by == 'popular':
        try:
            decks = decks.order_by('-clone_count')
        except:
            decks = decks.order_by('-created_at') 
    else:
        decks = decks.order_by('-created_at')

    paginator = Paginator(decks, 12)
    page_obj = paginator.get_page(page_number)

    data = []
    for deck in page_obj:
        data.append({
            'id': deck.id,
            'title': deck.title,
            'description': deck.description,
            'author': deck.user.username,
            'card_count': deck.cards.count(),
        })

    return JsonResponse({
        'results': data,
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number
    })