from django.db import models

'''
Models are the single, definitive source of information about your data.
They contain the essential fields and behaviors of the data you’re storing.
Generally, each model maps to a single database table.

This is the model for the pfp_table - contains functions for:
    - Tweet = pfp_table
TODO:
    - Add more models for other tables
    - Add models for viewing a specific user's data(?)
    - Change model names from Tweet to PFP_Table and propagate changes
'''


class Tweet(models.Model):
    index = models.CharField(
        max_length=255, primary_key=True, default='defaultUser')
    Name = models.CharField(max_length=255)
    Favorites = models.IntegerField()
    Retweets = models.IntegerField()
    Replies = models.IntegerField()
    Impressions = models.IntegerField()
    # Rank = models.IntegerField()
    # Global_Reach = models.IntegerField()
    PFP_Url = models.CharField(max_length=255)
    Description = models.CharField(max_length=255)
    Bio_Link = models.CharField(max_length=255)

    class Meta:
        # managed = False
        db_table = 'pfp_table'
        verbose_name_plural = 'pfp_table'

    def __str__(self):
        # print(f"{self.Name} has {self.Favorites} favorites, {self.Retweets} retweets, {self.Replies} replies, and {self.Impressions} impressions, and is ranked {self.Rank} with a global reach of {self.Global_Reach}, pfp url: {self.PFP_Url}, description: {self.Description}, and bio link: {self.Bio_Link}")
        # return f"{self.Name} has {self.Favorites} favorites, {self.Retweets} retweets, {self.Replies} replies, and {self.Impressions} impressions, and is ranked {self.Rank} with a global reach of {self.Global_Reach} pfp url: {self.PFP_Url}, description: {self.Description}, and bio link: {self.Bio_Link}"
        print(f"{self.Name} has {self.Favorites} favorites, {self.Retweets} retweets, {self.Replies} replies, and {self.Impressions} impressions, with  pfp url: {self.PFP_Url}, description: {self.Description}, and bio link: {self.Bio_Link}")
        return f"{self.Name} has {self.Favorites} favorites, {self.Retweets} retweets, {self.Replies} replies, and {self.Impressions} impressions, with pfp url: {self.PFP_Url}, description: {self.Description}, and bio link: {self.Bio_Link}"
