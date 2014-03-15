from django.shortcuts import render, get_object_or_404
from pieces.models import Piece, Keyword

import re

def view_piece(request, id):
    piece = get_object_or_404(Piece, pk=id)

    paragraphs = piece.content.split("\n")

    keywords = [kw.word for kw in Keyword.objects.filter(study=piece.study)]
    keyword_res = [re.compile(re.escape(word), re.IGNORECASE)
            for word in keywords]

    def add_highlights(text):
        def add_highight(t):
            return '<span style="color:red; font-weight:bold;">%s</span>' % t.group(0)

        for kwre in keyword_res:
            text, _ = kwre.subn(add_highight, text)

        return text

    content = "\n".join(
            "<p>%s</p>" % add_highlights(paragraph)
            for paragraph in paragraphs)

    return render(request, "pieces/piece.html", dict(piece=piece, content=content))

