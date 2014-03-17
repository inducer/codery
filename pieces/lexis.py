from __future__ import division
import re
import datetime

from django.db import transaction

C457_PARSE_RE = re.compile("^([-A-Z]+): (.*)$", re.MULTILINE)
DATE_ISH_PARSE_RE = re.compile(r"^([A-Za-z]+),? ([0-9]+)\, ([0-9]+)", re.MULTILINE)

from pieces.models import Piece, Venue, PieceToStudyAssociation


def get_venue(log_lines, venue_name, venue_type):
    venues = Venue.objects.filter(name=venue_name)
    if not venues:
        venue = Venue()
        venue.name = venue_name
        venue.publication_type = venue_type
        venue.save()
        return venue

    venue, = venues
    if venue.publication_type != venue_type:
        log_lines.append(
                "WARNING: Venue '%s' switched types from '%s' to '%s'"
                % (venue.name, venue.publication_type, venue_type))

    return venue


@transaction.atomic
def import_ln_html(log_lines, studies, html_file, create_date, creator):
    from bs4 import BeautifulSoup, Tag
    soup = BeautifulSoup(html_file.read())

    current_piece = None
    venue_type = None
    c012s = []
    extra_data = {}

    total_count = [0]
    import_count = [0]
    dupe_count = [0]

    def finalize_current_piece():
        if not c012s:
            return

        total_count[0] += 1

        extra_data["COPYRIGHT"] = c012s[-1]
        assert 3 <= len(c012s) <= 4, c012s
        venue_name = c012s[1].rstrip()
        current_piece.venue = get_venue(log_lines, venue_name, venue_type)

        current_piece.create_date = create_date
        current_piece.creator = creator

        from json import dumps
        current_piece.extra_data_json = dumps(extra_data)

        for piece in Piece.objects.filter(title=current_piece.title):
            if piece.content == current_piece.content:
                log_lines.append("Duplicate, not imported: %s"
                        % unicode(current_piece))
                dupe_count[0] += 1
                return

        import_count[0] += 1
        current_piece.save()

        for study in studies:
            pts = PieceToStudyAssociation()
            pts.study = study
            pts.piece = current_piece
            pts.create_date = create_date
            pts.creator = creator
            pts.save()

    for child in soup.body.children:
        if not isinstance(child, Tag):
            continue

        if child.name == "a":
            assert child["name"].startswith("DOC_ID_")
            if current_piece is not None:
                finalize_current_piece()

            current_piece = Piece()
            current_piece.content = ""

            log_lines.append("reading item %d..." % (total_count[0] + 2))
            c012s = []
            venue_type = None
            extra_data = {}

        if child.name == "br":
            continue

        if child.name == "div":
            div_class, = child["class"]
            p = child.p
            if p is None:
                continue
            p_class, = p["class"]
            span = p.span
            if span is None:
                continue

            span_class, = span["class"]
            text = child.get_text()

            key = (div_class, p_class, span_class)
            if key == ("c0", "c1", "c2"):
                c012s.append(text)
            elif key == ("c4", "c5", "c6"):
                current_piece.title = text.rstrip()
            elif key == ("c4", "c5", "c7"):
                match = C457_PARSE_RE.match(text)
                if match is None:
                    log_lines.append(
                            "WARNING: c457 did not match expected format: '%s'"
                            % text[:20].encode("ascii", errors="replace"))

                    continue

                field = match.group(1)
                value = match.group(2)

                if field == "BYLINE":
                    current_piece.byline = value.rstrip()
                elif field == "LOAD-DATE":
                    current_piece.source_load_date = \
                            datetime.datetime.strptime(value, "%B %d, %Y").date()
                elif field == "PUBLICATION-TYPE":
                    venue_type = value
                elif field == "URL":
                    current_piece.url = value.rstrip()
                else:
                    extra_data[field] = value.rstrip()

            elif key == ("c3", "c1", "c2"):
                date_match = DATE_ISH_PARSE_RE.match(text)

                current_piece.pub_date_unparsed = text.rstrip()

                if date_match is None:
                    log_lines.append(
                            "WARNING: c312 did not match expected "
                            "date-ish format: '%s'"
                            % text[:20].encode("ascii", errors="replace"))
                else:
                    month = date_match.group(1)
                    day = date_match.group(2)
                    year = date_match.group(3)

                    rebuilt_pub_date = "%s %s, %s" % (month, day, year)
                    current_piece.pub_date = datetime.datetime.strptime(
                            rebuilt_pub_date, "%B %d, %Y").date()

            elif key in [
                    ("c4", "c8", "c2"),
                    ("c4", "c8", "c7"),
                    ("c4", "c8", "c9"),
                    ("c4", "c5", "c2"),
                    ("c4", "c8", "c11"),
                    ]:
                # body text

                current_piece.content += text
            else:
                #print text
                raise RuntimeError(
                        "unknown doc key: %s" % str(key))

    finalize_current_piece()

    log_lines = [ll.replace("\n", "<newline>") for ll in log_lines]
    log_lines.append("%d items total, %d imported, %d duplicate"
            % (total_count[0], import_count[0], dupe_count[0]))

    return log_lines
