from django.contrib import admin
from .models import Profile, Deck, Flashcard
from .models import DictionaryWord

admin.site.register(Profile)
admin.site.register(Deck)
admin.site.register(Flashcard)

@admin.register(DictionaryWord)
class DictionaryWordAdmin(admin.ModelAdmin):
    list_display = ('word', 'meaning', 'language')
    list_filter = ('language',)
    search_fields = ('word', 'meaning')