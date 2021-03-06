from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

import six


class Venue(models.Model):
    name = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name

    if six.PY3:
        __str__ = __unicode__

    class Meta:
        ordering = ["name"]


class Study(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    coding_tool_url = models.URLField(null=True, blank=True)

    urls_clickable = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "studies"

    def __str__(self):
        return self.name


class keyword_rule:
    substring = "sub"
    word = "word"
    word_wildcard = "word_wildcard"
    regular_expression = "regex"


KW_RULE_CHOICES = (
        (keyword_rule.substring, "Substring"),
        (keyword_rule.word, "Word"),
        (keyword_rule.word_wildcard, "Word with wildcards"),
        (keyword_rule.regular_expression, "Regular expression"),
        )

COLOR_CHOICES = (
        ("red", "Red"),
        ("green", "Green"),
        ("blue", "Blue"),
        ("cyan", "Cyan"),
        ("magenta", "Magenta"),
        ("black", "Black"),
        )


class Keyword(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    rule = models.CharField(
            max_length=20, choices=KW_RULE_CHOICES,
            help_text="The 'Substring' rule matches any occurrence "
            "of the pattern anywhere. For example, 'flu' would match "
            "'influence'.\n"
            "The 'Word' rule matches only entire words.\n"
            "The 'Word wildcard' rule matches entire words against "
            "a pattern with * (any number of characters, including zero) "
            "and ? (single character) wildcards. For example, '*at' "
            "would match 'cat' and 'brat', but not 'dedication'.\n"
            "Regular expressions allow very general matching. "
            "Search the Internt for 'python re' to learn more."
            )
    pattern = models.CharField(max_length=1000)
    color = models.CharField(max_length=50, choices=COLOR_CHOICES)

    def __unicode__(self):
        return "%s: %s" % (self.rule, self.pattern)

    if six.PY3:
        __str__ = __unicode__

    def get_re(self):
        import re
        if self.rule == keyword_rule.substring:
            return re.escape(self.pattern)
        elif self.rule == keyword_rule.word:
            return r"\b" + re.escape(self.pattern) + r"\b"
        elif self.rule == keyword_rule.word_wildcard:
            result = r"\b" + re.escape(self.pattern) + r"\b"
            result = (result
                    .replace(r"\*", r"\S*?")
                    .replace(r"\?", "\S"))
            return result
        elif self.rule == keyword_rule.regular_expression:
            return self.pattern
        else:
            raise RuntimeError("invalid keyword rule")


DUPLICATE_PIECE_TAG = "duplicate"
AUTOMATIC_PIECE_TAGS = [DUPLICATE_PIECE_TAG]


class PieceTag(models.Model):
    name = models.CharField(max_length=100, unique=True,
            help_text="Recommended format is lower-case-with-hyphens. "
            "Do not use spaces.")
    create_date = models.DateTimeField(default=now)
    shown_to_coders = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    if six.PY3:
        __str__ = __unicode__

    class Meta:
        permissions = (
            ("tag_by_search",
                "Can assign piece tags to search result"),
            ("may_see_non_coder_tags",
                "May see non-coder tags"),
            )


def get_piece_tag(name):
    tags = PieceTag.objects.filter(name=name)
    if not tags:
        tag = PieceTag()
        tag.name = name
        tag.save()
        return tag

    tag, = tags
    return tag


class Piece(models.Model):
    title = models.CharField(max_length=1000, blank=True)
    content = models.TextField(blank=True)

    publication_type = models.CharField(max_length=200, null=True)

    notes = models.TextField(null=True, blank=True)

    studies = models.ManyToManyField(Study,
            through='PieceToStudyAssociation')

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    pub_date = models.DateField(null=True, blank=True)
    pub_date_unparsed = models.CharField(max_length=1000, null=True, blank=True)

    source_load_date = models.DateField(null=True, blank=True)

    byline = models.CharField(max_length=1000, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    create_date = models.DateTimeField(default=now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    extra_data_json = models.TextField(null=True, blank=True)

    tags = models.ManyToManyField(PieceTag, verbose_name="piece tag")

    def get_absolute_url(self):
        return "/piece/%d/" % self.id

    def display_title(self):
        if self.title:
            if len(self.title) > 30:
                return self.title[:30]+"..."
            else:
                return self.title
        else:
            return "(no title)"

    def __unicode__(self):
        if self.id is None:
            id_str = "(no ID)"
        else:
            id_str = str(self.id)

        return "%s: %s" % (id_str, self.display_title())

    if six.PY3:
        __str__ = __unicode__

    class Meta:
        ordering = ["-pub_date", "title"]

        permissions = (
                ("bulk_import", "Can import pieces in bulk"),
                )


class PieceToStudyAssociation(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE)
    piece = models.ForeignKey(Piece, on_delete=models.CASCADE)

    create_date = models.DateTimeField(default=now)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __unicode__(self):
        return u"%s - %s" % (self.piece, self.study)

    if six.PY3:
        __str__ = __unicode__
