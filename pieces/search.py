from django.shortcuts import render
import django.forms as forms

from django.contrib.auth.decorators import login_required

from django.contrib import messages

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from pytools.lex import RE as REBase

from pieces.models import PieceTag, Piece


# {{{ parsing

# {{{ lexer data

_and = intern("and")
_or = intern("or")
_not = intern("not")
_openpar = intern("openpar")
_closepar = intern("closepar")
_id = intern("id")
_tag = intern("tag")
_regex = intern("regex")
_word = intern("word")
_near = intern("near")
_fulltext = intern("fulltext")
_whitespace = intern("whitespace")

# }}}


class RE(REBase):
    def __init__(self, s):
        import re
        super(RE, self).__init__(s, re.UNICODE)


_LEX_TABLE = [
    (_and, RE(r"and\b")),
    (_or, RE(r"or\b")),
    (_not, RE(r"not\b")),
    (_openpar, RE(r"\(")),
    (_closepar, RE(r"\)")),
    (_id, RE(r"id:([0-9]+)")),
    (_tag, RE(r"tag:([-\w]+)")),
    (_regex, RE(r"regex:(\S+)")),
    (_word, RE(r"word:(\S+)")),
    (_near, RE(r"near:([1-9]),(\w+),(\w+)")),
    (_fulltext, RE(r'".*?(?!\\\\)"')),
    (_whitespace, RE("[ \t]+")),
    ]


_TERMINALS = ([_tag, _fulltext, _id])

# {{{ operator precedence

_PREC_OR = 10
_PREC_AND = 20
_PREC_NOT = 30

# }}}


# {{{ parser

def parse_query(expr_str):
    from django.db.models import Q

    def parse_terminal(pstate):
        next_tag = pstate.next_tag()
        if next_tag is _tag:
            tag = PieceTag.objects.get(
                    name=pstate.next_match_obj().group(1))
            result = Q(tags__id=tag.id)
            pstate.advance()
            return result
        elif next_tag is _regex:
            re_value = pstate.next_match_obj().group(1)
            pstate.advance()
            return Q(content__iregex=re_value) | Q(title__iregex=re_value)
        elif next_tag is _word:
            re_value = r"\b%s\b" % pstate.next_match_obj().group(1)
            pstate.advance()
            return Q(content__iregex=re_value) | Q(title__iregex=re_value)
        elif next_tag is _near:
            match_obj = pstate.next_match_obj()
            dist = int(match_obj.group(1))
            word1 = match_obj.group(2)
            word2 = match_obj.group(3)

            regexes = []
            for first_word, second_word in [(word1, word2), (word2, word1)]:
                for i in range(0, dist):
                    regex = r"\b%s" % first_word
                    for j in range(i):
                        regex += "\W+\w+"
                    regex += r"\W+%s\b" % second_word
                    regexes.append(regex)
            re_value = "|".join(regexes)
            print re_value
            pstate.advance()
            return Q(content__iregex=re_value) | Q(title__iregex=re_value)
        elif next_tag is _fulltext:
            text = pstate.next_str_and_advance()[1:-1]
            return Q(content__icontains=text) | Q(title__icontains=text)
        elif next_tag in [_id]:
            result = Q(id=int(pstate.next_match_obj().group(1)))
            pstate.advance()
            return result
        else:
            pstate.expected("terminal")

    def inner_parse(pstate, min_precedence=0):
        pstate.expect_not_end()

        if pstate.is_next(_not):
            pstate.advance()
            left_query = ~inner_parse(pstate, _PREC_NOT)
        elif pstate.is_next(_openpar):
            pstate.advance()
            left_query = inner_parse(pstate)
            pstate.expect(_closepar)
            pstate.advance()
        else:
            left_query = parse_terminal(pstate)

        did_something = True
        while did_something:
            did_something = False
            if pstate.is_at_end():
                return left_query

            next_tag = pstate.next_tag()

            if next_tag is _and and _PREC_AND > min_precedence:
                pstate.advance()
                left_query = left_query & inner_parse(pstate, _PREC_AND)
                did_something = True
            elif next_tag is _or and _PREC_OR > min_precedence:
                pstate.advance()
                left_query = left_query | inner_parse(pstate, _PREC_OR)
                did_something = True
            elif (next_tag in _TERMINALS + [_not, _openpar]
                    and _PREC_AND > min_precedence):
                left_query = left_query & inner_parse(pstate, _PREC_AND)
                did_something = True

        return left_query

    from pytools.lex import LexIterator, lex
    pstate = LexIterator(
        [(tag, s, idx, matchobj)
         for (tag, s, idx, matchobj) in lex(_LEX_TABLE, expr_str, match_objects=True)
         if tag is not _whitespace], expr_str)

    if pstate.is_at_end():
        pstate.raise_parse_error("unexpected end of input")

    result = inner_parse(pstate)
    if not pstate.is_at_end():
        pstate.raise_parse_error("leftover input after completed parse")

    return result

# }}}

# }}}


# {{{ search form

class SearchForm(forms.Form):
    def __init__(self, assign_tag_allowed, large_query, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-1"
        self.helper.field_class = "col-lg-8"

        widget = None
        if large_query:
            widget = forms.Textarea

        self.fields["query"] = forms.CharField(min_length=1, widget=widget,
                help_text="""
                The following search syntax is supported:
                <code>"<i>fulltext</i>"</code>,
                <code>word:<i>someword</i></code>,
                <code>near:<i>3</i>,<i>someword</i>,<i>otherword</i></code>,
                <code>id:<i>1234</i></code>,
                <code>tag:<i>piece-tag</i></code>,
                <code>regex:<i>regular-expression</i></code>.
                """)
        if assign_tag_allowed:
            self.fields["tag"] = forms.ModelChoiceField(
                    queryset=PieceTag.objects,
                    help_text="If you click 'Assign tag' or 'Remove tag', this tag "
                    "will be assigned to or removed from every piece in "
                    "the result set",
                    required=False)

        self.fields["query"].widget.attrs["autofocus"] = None

        self.helper.add_input(
                Submit("search", "Search", css_class="col-lg-offset-1"))
        if assign_tag_allowed:
            self.helper.add_input(
                    Submit("assign_tag", "Assign tag"))
            self.helper.add_input(
                    Submit("remove_tag", "Remove tag"))


@login_required
def view_search_form(request, large_query=False):
    assign_tag_allowed = request.user.has_perm("tag_by_search")

    pieces = None
    if request.method == "POST":
        form = SearchForm(
                assign_tag_allowed,
                large_query,
                request.POST, request.FILES)
        assign_tag = assign_tag_allowed and "assign_tag" in request.POST
        remove_tag = assign_tag_allowed and "remove_tag" in request.POST

        if form.is_valid():
            try:
                query = parse_query(
                        form.cleaned_data["query"].replace("\n", " "))
                pieces = (Piece.objects
                        .filter(query)
                        .select_related("tags"))
            except Exception as e:
                messages.add_message(request, messages.ERROR,
                        type(e).__name__+": "+str(e))
            else:
                tag = form.cleaned_data["tag"]

                if assign_tag:
                    count = 0
                    for piece in pieces:
                        if tag not in piece.tags.all():
                            piece.tags.add(tag)
                            piece.save()
                            count += 1
                    messages.add_message(request, messages.INFO,
                            "%d tags assigned." % count)

                if remove_tag:
                    count = 0
                    for piece in pieces:
                        if tag in piece.tags.all():
                            piece.tags.remove(tag)
                            piece.save()
                            count += 1
                    messages.add_message(request, messages.INFO,
                            "%d tags removed." % count)

    else:
        form = SearchForm(assign_tag_allowed, large_query)

    return render(request, 'pieces/search.html', {
        "form": form,
        "pieces": pieces,
        "may_see_non_coder_tags": request.user.has_perm("may_see_non_coder_tags"),
        "count": pieces.count() if pieces is not None else 0,
    })


@login_required
def view_large_search_form(request):
    return view_search_form(request, large_query=True)

# }}}

# vim: foldmethod=marker
