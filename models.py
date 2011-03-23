from django.db import models
from django.contrib.auth import models as auth_models

class Project(models.Model):
    name          = models.CharField(max_length=32)
    creation_date = models.DateTimeField(auto_now=True)

    @property
    def user_set(self):
        return self.entry_set.values

    def __unicode__(self):
        return self.name

class Entry(models.Model):
    project       = models.ForeignKey(Project)
    creator       = models.ForeignKey(auth_models.User, related_name='created_entry_set')
    user          = models.ForeignKey(auth_models.User)
    amount        = models.FloatField()

    def __unicode__(self):
        return u"%s - %s" %(self.amount,
                            self.project)
