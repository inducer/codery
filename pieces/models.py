from django.db import models

class Venue(models.Model):
    name = models.CharField(max_length=200)
    publication_type = models.CharField(max_length=200, null=True)

    def __unicode__(self):
        return self.name


class Study(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

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
    content = models.TextField(max_length=1000, blank=True)

    study = models.ForeignKey(Study)
    venue = models.ForeignKey(Venue)
    pub_date = models.DateField(null=True, blank=True)
    pub_date_unparsed = models.CharField(max_length=1000, null=True, blank=True)
    load_date = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=1000, null=True, blank=True)
    byline = models.CharField(max_length=1000, null=True, blank=True)
    copyright = models.CharField(max_length=1000, null=True, blank=True)
    document_type = models.CharField(max_length=1000, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    dateline = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        if self.title:
            return self.title
        else:
            return "(no title)"

    def get_absolute_url(self):
        return "/piece/%d" % self.id

    class Meta:
        ordering = ["-pub_date", "title"]

        permissions = (
                ("bulk_import", "Can import pieces in bulk"),
                )
