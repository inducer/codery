from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


class Venue(models.Model):
    name = models.CharField(max_length=200)
    publication_type = models.CharField(max_length=200, null=True)

    def __unicode__(self):
        return self.name


class Study(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    coding_tool_url = models.URLField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "studies"

    def __unicode__(self):
        return self.name


class Keyword(models.Model):
    study = models.ForeignKey(Study)
    word = models.CharField(max_length=200)

    def __unicode__(self):
        return self.word


class Piece(models.Model):
    title = models.CharField(max_length=1000, blank=True)
    content = models.TextField(blank=True)

    notes = models.TextField(null=True, blank=True)

    studies = models.ManyToManyField(Study,
            through='PieceToStudyAssociation')

    venue = models.ForeignKey(Venue)
    pub_date = models.DateField(null=True, blank=True)
    pub_date_unparsed = models.CharField(max_length=1000, null=True, blank=True)

    source_load_date = models.DateField(null=True, blank=True)

    byline = models.CharField(max_length=1000, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    create_date = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User)

    extra_data_json = models.TextField(null=True, blank=True)

    def __unicode__(self):
        if self.title:
            if len(self.title) > 30:
                return self.title[:30]+"..."
            else:
                return self.title
        else:
            return "(no title)"

    #def get_absolute_url(self):
        #return "/piece/%d" % self.id

    class Meta:
        ordering = ["-pub_date", "title"]

        permissions = (
                ("bulk_import", "Can import pieces in bulk"),
                )


class PieceToStudyAssociation(models.Model):
    study = models.ForeignKey(Study)
    piece = models.ForeignKey(Piece)

    create_date = models.DateTimeField(default=datetime.now)
    creator = models.ForeignKey(User)

    def __unicode__(self):
        return u"%s - %s" % (self.piece, self.study)
