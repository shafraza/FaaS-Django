from django.contrib import admin
from .models import Category, Pic
from django.utils.html import format_html
from django.contrib.auth import get_user_model

User = get_user_model()

if not admin.site.is_registered(Category):
    class CategoryAdmin(admin.ModelAdmin):
        list_display = ('name', 'id', 'pic_count',)
        search_fields = ['name']
        list_filter = ['name']
        ordering = ['name']
        list_per_page = 20 
        fieldsets = (
            (None, {
                'fields': ('name',)
            }),
        )
        
        def pic_count(self, obj):
            return obj.pics.count()
        pic_count.short_description = 'Number of Pics'

        def view_pics_link(self, obj):
            return format_html('<a href="/admin/app/pic/?category__id__exact={}">View Pics</a>', obj.id)
        view_pics_link.short_description = 'View Pics'


admin.site.register(Category, CategoryAdmin)


class PicAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'size', 'created', 'updated', 'image_preview')
    search_fields = ['name', 'description', 'owner__username', 'category__name']
    list_filter = ['category', 'size', 'created']
    ordering = ['-created']
    list_per_page = 20  
    raw_id_fields = ('owner', 'category')  
    date_hierarchy = 'created' 
    actions = ['make_pics_large']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Image Preview'

    def make_pics_large(self, request, queryset):
        updated_count = queryset.update(size='L')
        self.message_user(request, f'{updated_count} photos were updated to Large size.')
    make_pics_large.short_description = 'Mark selected pictures as Large'

admin.site.register(Pic, PicAdmin)
