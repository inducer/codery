from __future__ import division
import re
import datetime

from django.db import transaction

C457_PARSE_RE = re.compile("^([-A-Z]+):\s+(.*)$", re.MULTILINE | re.UNICODE)
DATE_ISH_PARSE_RE = re.compile(r"^([A-Za-z]+),? ([0-9]+)\, ([0-9]+)", re.MULTILINE)

from pieces.models import (Piece, Venue,
        PieceToStudyAssociation, get_piece_tag,
        DUPLICATE_PIECE_TAG)


def get_venue(log_lines, venue_name):
    venue_name = venue_name.strip()

    venues = Venue.objects.filter(name=venue_name)
    if not venues:
        venue = Venue()
        venue.name = venue_name
        venue.save()
        return venue

    venue, = venues

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
def import_ln_html(log_lines, studies, html_file, tags, repair_content,
        create_date, creator):
    from bs4 import BeautifulSoup, Tag
    soup = BeautifulSoup(html_file.read())

    total_count = [0]
    import_count = [0]

    dupe_tag = get_piece_tag(DUPLICATE_PIECE_TAG)

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
        current_piece.venue = get_venue(log_lines, venue_name)

        if repair_content:
            log_lines.append("Repairing: item %d (marked '%s'), titled '%s'..."
                    % (total_count[0], upload_ordinal, current_piece.title))
            pieces_to_repair = Piece.objects.filter(
                    title=current_piece.title,
                    venue=current_piece.venue,
                    publication_type=current_piece.publication_type,
                    pub_date_unparsed=current_piece.pub_date_unparsed,
                    byline=current_piece.byline,
                    source_load_date=current_piece.source_load_date)

            repair_count = 0
            for piece_to_repair in pieces_to_repair:
                log_lines.append(
                        "  Repairing ID %d, previous content length: "
                        "%d characters, new: %d characters"
                        % (piece_to_repair.id, len(piece_to_repair.content),
                            len(current_piece.content)))
                piece_to_repair.content = current_piece.content
                piece_to_repair.save()
                repair_count += 1

            if repair_count:
                log_lines.append("  Repaired %d pieces" % repair_count)
            else:
                log_lines.append("  WARNING! No pieces repaired.")

            return

        new_tags = list(tags)

        for piece in (Piece.objects
                    .filter(title=current_piece.title)
                    .exclude(tags__id=dupe_tag.id)):
            if (piece.content == current_piece.content
                    and piece.venue == current_piece.venue):
                new_tags.append(dupe_tag)
                extra_data["CODERY_DUPLICATE_OF"] = piece.id
                break

        current_piece.create_date = create_date
        current_piece.creator = creator

        from json import dumps
        current_piece.extra_data_json = dumps(extra_data)

        import_count[0] += 1
        current_piece.save()

        current_piece.tags = new_tags
        current_piece.save()

        if not current_piece.content:
            log_lines.append("WARNING: Empty content in item %d (marked '%s')"
                    % (total_count[0], upload_ordinal))
        if not current_piece.title:
            log_lines.append("WARNING: no title on item %d (marked '%s')..."
                    % (total_count[0], upload_ordinal))

        log_lines.append("imported item %d (marked '%s'), "
                "%d characters in title, %d characters in body..."
                % (
                    total_count[0], upload_ordinal,
                    len(current_piece.title),
                    len(current_piece.content),
                    ))

        for study in studies:
            pts = PieceToStudyAssociation()
            pts.study = study
            pts.piece = current_piece
            pts.create_date = create_date
            pts.creator = creator
            pts.save()

    # }}}

    current_piece = None
    c012s = []
    extra_data = {}

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
            extra_data = {}

        if child.name == "br":
            continue

        if child.name == "div":
            div_class, = child["class"]

            for potential_p in child.children:
                if potential_p.name != "p":
                    continue
                p = potential_p

                p_class, = p["class"]
                span = p.span
                if span is None:
                    continue

                span_class, = span["class"]
                text = p.get_text()+"\n\n"
                loggable_text = text.rstrip()[:20].encode("ascii", errors="replace")

                key = "".join([div_class, p_class, span_class])

                if key == "c0c1c2":
                    c012s.append(text.rstrip())
                elif key in ["c4c5c6", "c5c6c7"]:
                    current_piece.title = text.rstrip()
                elif (
                        key.startswith("c5c6")
                        or key in ["c4c5c7", "c5c6c8", "c5c6c2"]
                        ):
                    match = C457_PARSE_RE.match(text)
                    if match is None:
                        log_lines.append(
                                "WARNING: %s did not match expected format: "
                                "'%s' (%d characters total)"
                                % (key, loggable_text, len(text)))

                        continue

                    field = match.group(1)
                    value = match.group(2).rstrip()

                    if field == "BYLINE":
                        current_piece.byline = value
                    elif field == "LOAD-DATE":
                        current_piece.source_load_date = \
                                parse_date_leniently(value)
                    elif field == "PUBLICATION-TYPE":
                        current_piece.publication_type = value
                    elif field == "URL":
                        current_piece.url = value
                    else:
                        extra_data[field] = value

                elif key.startswith("c3c1"):
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

                elif (key.startswith("c4c8")
                        or key.startswith("c5c9")
                        or key.startswith("c5c10")
                        or key in [
                            "c4c5c2"
                            ]):
                    # body text

                    current_piece.content += text
                elif key in ["c5c6c15", "c4c5c13"]:
                    # header text
                    pass
                else:
                    # print text
                    raise RuntimeError("unknown doc key: %s" % key)

    finalize_current_piece()

    new_log_lines = [ll.replace("\n", "[newline]") for ll in log_lines]
    new_log_lines.append("%d items total, %d imported"
            % (total_count[0], import_count[0]))

    log_lines[:] = new_log_lines

# vim: foldmethod=marker
