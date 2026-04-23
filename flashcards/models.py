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