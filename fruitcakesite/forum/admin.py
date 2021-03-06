from django.contrib import admin
from forum.models import UserProfile, Forum, Thread, Post
### Admin


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "date_joined", "shipments", "posts", "avatar"]
    list_filter = ('shipments', 'posts',)

class ForumAdmin(admin.ModelAdmin):
    list_display = ["title"]

class ThreadAdmin(admin.ModelAdmin):
    list_display = ["title", "forum", "creator", "created"]
    list_filter = ["forum", "creator"]

class PostAdmin(admin.ModelAdmin):
    search_fields = ["title", "creator"]
    list_display = ["title", "thread", "creator", "created"]

admin.site.register(Forum, ForumAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(UserProfile, ProfileAdmin)


