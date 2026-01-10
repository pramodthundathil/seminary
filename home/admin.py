from django.contrib import admin
from .models import Sliders, SliderPhotos

# Register your models here.
class SliderPhotosInline(admin.TabularInline):
    model = SliderPhotos
    extra = 1

@admin.register(Sliders)
class SlidersAdmin(admin.ModelAdmin):
    list_display = ('slider_name', 'code', 'width', 'height')
    inlines = [SliderPhotosInline]

@admin.register(SliderPhotos)
class SliderPhotosAdmin(admin.ModelAdmin):
    list_display = ('title', 'sliders', 'media', 'created_at')
