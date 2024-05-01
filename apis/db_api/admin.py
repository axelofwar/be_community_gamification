from django.contrib import admin
from .models import Tweet


class PFP_TableAdmin(admin.ModelAdmin):
    """
    Admin model for database navigation via API
    """
    list_display = ("Name", "Favorites", "Retweets", "Replies", "Impressions",
                    "Rank", "Global_Reach", "PFP_Url", "Description", "Bio_Link")
    list_filter = ("Name", "Favorites", "Retweets", "Replies", "Impressions",
                   "Rank", "Global_Reach", "PFP_Url", "Description", "Bio_Link")
    search_fields = ("Name", "Favorites", "Retweets", "Replies", "Impressions",
                     "Rank", "Global_Reach", "PFP_Url", "Description", "Bio_Link")


# Register your models here.
'''
admin.py is the configuration file for the admin site
This file is used to configure the admin site, and is automatically generated when the app is created

We can use this file to add models to the admin site, and to configure the admin site
This gives django access to the database tables and their data, and allows us to view and edit the data from the admin site interface
'''
admin.site.register(Tweet, PFP_TableAdmin)
