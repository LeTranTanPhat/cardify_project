from django import forms
from .models import Deck, Flashcard

class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['title', 'description']
        # Thêm class của Bootstrap để form đẹp hơn
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: Từ vựng IELTS...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Nhập mô tả ngắn gọn cho bộ thẻ...'}),
        }

# THÊM ĐOẠN NÀY VÀO CUỐI FILE
class FlashcardForm(forms.ModelForm):
    class Meta:
        model = Flashcard
        fields = ['front_side', 'back_side']
        widgets = {
            'front_side': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Nhập từ vựng/câu hỏi...'}),
            'back_side': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Nhập định nghĩa/đáp án...'}),
        }