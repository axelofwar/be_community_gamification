from django.contrib import admin
from .models import Tweet


class PFP_TableAdmin(admin.ModelAdmin):
    list_display = ("Name", "Favorites", "Retweets", "Replies", "Impressions")
    list_filter = ("Name", "Favorites", "Retweets", "Replies", "Impressions")
    search_fields = ("Name", "Favorites", "Retweets", "Replies", "Impressions")


admin.site.register(Tweet, PFP_TableAdmin)


# Register your models here.
'''
admin.py is the configuration file for the admin site
This file is used to configure the admin site, and is automatically generated when the app is created

We can use this file to add models to the admin site, and to configure the admin site
This gives django access to the database tables and their data, and allows us to view and edit the data from the admin site interface
'''
