from django.db import models
from django.contrib.auth.models import User

# 1. Quản lý Nhân vật (Game hóa)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.IntegerField(default=1)
    xp = models.IntegerField(default=0)
    energy = models.IntegerField(default=100)
    hearts = models.IntegerField(default=5) # Tối đa 5 tim

    def __str__(self):
        return f"{self.user.username} - LVL {self.level}"

# 2. Bộ thẻ (Hỗ trợ Kho thẻ cộng đồng)
class Deck(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False) # True = Đưa lên Kho thẻ cộng đồng
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# 3. Thẻ Flashcard
class Flashcard(models.Model):
    deck = models.ForeignKey(Deck, related_name='cards', on_delete=models.CASCADE)
    front_side = models.TextField()
    back_side = models.TextField()
    
    def __str__(self):
        return self.front_side
    
class DictionaryWord(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'Tiếng Anh'),
        ('zh', 'Tiếng Trung'),
        ('ko', 'Tiếng Hàn'),
    ]
    word = models.CharField(max_length=255, verbose_name="Từ vựng")
    meaning = models.TextField(verbose_name="Ý nghĩa")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en', verbose_name="Ngôn ngữ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.word} ({self.language})"
    
# 4. Model lưu thông tin tổng quát của một phiên học
class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE) 
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    cards_reviewed = models.IntegerField(default=0) # Tổng số thẻ đã lật
    correct_answers = models.IntegerField(default=0) # Số thẻ nhấn "Nhớ"
    xp_gained = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.deck.title} - {self.start_time.strftime('%d/%m/%Y')}"

# 5. Model lưu tiến độ của từng thẻ bài (Đã sửa lỗi Card -> Flashcard)
class CardProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Sửa từ 'Card' thành 'Flashcard' để khớp với định nghĩa bên trên
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE) 
    box_number = models.IntegerField(default=1) # Cấp độ thuộc: 1 (mới), 5 (rất thuộc)
    last_reviewed = models.DateTimeField(auto_now=True)
    is_mastered = models.BooleanField(default=False)

    class Meta:
        # Đảm bảo mỗi user chỉ có duy nhất một trạng thái tiến độ cho mỗi thẻ bài
        unique_together = ('user', 'card')

    def __str__(self):
        return f"{self.user.username} - {self.card.front_side[:20]} - Lv.{self.box_number}"