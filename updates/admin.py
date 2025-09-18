from django.contrib import admin
from .models import Update, Comment, Like, UpdateReadState


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'published')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'update', 'parent', 'created_at')


admin.site.register(Like)
admin.site.register(UpdateReadState)
