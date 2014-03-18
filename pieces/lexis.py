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
                "WARNING: Venue '%s' switched types from '%s' (in database) "
                "to '%s' (in imported piece)"
                % (venue.name, venue.publication_type, venue_type))

    return venue


def parse_date_leniently(text):
    date_match = DATE_ISH_PARSE_RE.match(text)

    if date_match is not None:
        month = date_match.group(1)
        day = date_match.group(2)
        year = date_match.group(3)

        rebuilt_pub_date = "%s %s, %s" % (month, day, year)
        return datetime.datetime.strptime(
                rebuilt_pub_date, "%B %d, %Y")
    else:
        return None


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

    # {{{ piece finalization

    def finalize_current_piece():
        if not c012s:
            return

        total_count[0] += 1

        extra_data["COPYRIGHT"] = c012s[-1]
        assert 3 <= len(c012s) <= 4, c012s

        extra_data["CODERY_LN_UPLOAD_NAME"] = html_file.name
        upload_ordinal = extra_data["CODERY_LN_UPLOAD_ORDINAL"] = c012s[0].rstrip()

        venue_name = c012s[1].rstrip()
        current_piece.venue = get_venue(log_lines, venue_name, venue_type)

        current_piece.create_date = create_date
        current_piece.creator = creator

        from json import dumps
        current_piece.extra_data_json = dumps(extra_data)

        if not current_piece.title:
            log_lines.append("WARNING: no title on item %d (marked '%s')..."
                    % (total_count[0], upload_ordinal))

        for piece in Piece.objects.filter(title=current_piece.title):
            if (piece.content == current_piece.content
                    and piece.venue == current_piece.venue):
                log_lines.append("did not import item %d "
                        "-- duplicate (marked '%s')..."
                        % (total_count[0], upload_ordinal))
                dupe_count[0] += 1
                return

        import_count[0] += 1
        current_piece.save()

        log_lines.append("imported item %d (marked '%s')..."
                % (total_count[0], upload_ordinal))

        for study in studies:
            pts = PieceToStudyAssociation()
            pts.study = study
            pts.piece = current_piece
            pts.create_date = create_date
            pts.creator = creator
            pts.save()

    # }}}

    for child in soup.body.children:
        if not isinstance(child, Tag):
            continue

        if child.name == "a":
            assert child["name"].startswith("DOC_ID_")
            if current_piece is not None:
                finalize_current_piece()

            current_piece = Piece()
            current_piece.content = ""

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
            loggable_text = text.rstrip()[:20].encode("ascii", errors="replace")

            key = "".join([div_class, p_class, span_class])

            if key == "c0c1c2":
                c012s.append(text.rstrip())
            elif key in ["c4c5c6", "c5c6c7"]:
                current_piece.title = text.rstrip()
            elif key in ["c4c5c7", "c5c6c8"]:
                match = C457_PARSE_RE.match(text)
                if match is None:
                    log_lines.append(
                            "WARNING: c457 did not match expected format: '%s'"
                            % loggable_text)

                    continue

                field = match.group(1)
                value = match.group(2).rstrip()

                if field == "BYLINE":
                    current_piece.byline = value
                elif field == "LOAD-DATE":
                    current_piece.source_load_date = \
                            parse_date_leniently(value)
                elif field == "PUBLICATION-TYPE":
                    venue_type = value
                elif field == "URL":
                    current_piece.url = value
                else:
                    extra_data[field] = value

            elif key in ["c3c1c2", "c3c1c4"]:
                parsed_date = parse_date_leniently(text)

                if parsed_date is None:
                    log_lines.append(
                            "WARNING: %s did not match expected "
                            "date-ish format: '%s', treating as c012"
                            % (key, loggable_text))
                    c012s.append(text.rstrip())
                else:
                    current_piece.pub_date_unparsed = text.rstrip()
                    current_piece.pub_date = parsed_date

            elif key in [
                    "c4c8c2",
                    "c4c8c7",
                    "c4c8c9",
                    "c4c5c2",
                    "c4c8c11",
                    "c5c9c2",
                    ]:
                # body text

                current_piece.content += text
            else:
                #print text
                raise RuntimeError("unknown doc key: %s" % key)

    finalize_current_piece()

    log_lines = [ll.replace("\n", "<newline>") for ll in log_lines]
    log_lines.append("%d items total, %d imported, %d duplicate"
            % (total_count[0], import_count[0], dupe_count[0]))

    return log_lines

# vim: foldmethod=marker
