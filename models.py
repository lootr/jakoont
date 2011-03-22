from django.db import models

class Project(models.Model):
    name          = models.CharField(max_length=32)
    creation_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

class Entry(models.Model):
    project       = models.ForeignKey(Project)
#    user          = models.ForeignKey(User)
    amount        = models.FloatField()

    def __unicode__(self):
        return u"%s - %s" %(self.amount,
                            self.project)
