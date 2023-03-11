from django.urls import path
from db_api.views import pfpTable, adminPfpTable, Index, UpdateRule, RemoveRule

app_name = 'db_api'

'''
This is the URL configuration for the db_api app - contains functions for:
    - PFPTable = pfp_table
    - TweetDetail = pfp_table detail 

TODO:
    - Add more views for other tables
    - Add views for viewing a specific user's data(?)
    - Change api names from Tweet to PFP_Table and propagate changes
'''
urlpatterns = [
    path('leaderboard/', pfpTable.as_view(), name='PFP_Table'),
    path('admin/', adminPfpTable.as_view(), name='PFP_Table_detail'),
    path('/', Index.as_view, name='index'),
    path('add-rule/', UpdateRule.as_view(), name='add-rule'),
    path('remove-rule/', RemoveRule.as_view(), name='remove-rule'),
]
