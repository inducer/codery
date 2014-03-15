from __future__ import division
import sys
import re
import datetime

C457_PARSE_RE = re.compile("^([-A-Z]+): (.*)$", re.MULTILINE)
DATE_ISH_PARSE_RE = re.compile(r"^([A-Za-z]+),? ([0-9]+)\, ([0-9]+)", re.MULTILINE)

from pieces.models import Piece, Venue, Study

from warnings import warn

def get_venue(venue_name, venue_type):
    venues = Venue.objects.filter(name=venue_name)
    if not venues:
        venue = Venue()
        venue.name = venue_name
        venue.publication_type = venue_type
        venue.save()
        return venue

    venue, = venues
    if venue.publication_type != venue_type:
        warn("Venue '%s' switched types from '%s' to '%s'"
            % (venue.name, venue.publication_type, venue_type))

    return venue


def main():
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] HTML_FILE")
    parser.add_option("--study-id", type="int", metavar="STUDY_ID")

    options, args = parser.parse_args()

    if not len(args) == 1:
        parser.print_usage()
        sys.exit(1)

    if options.study_id is None:
        raise RuntimeError("must pass --study-id=NUMBER")

    from bs4 import BeautifulSoup, Tag
    with open(args[0], "rt") as html_file:
        soup = BeautifulSoup(html_file.read())

    study, = Study.objects.filter(id=options.study_id)

    current_piece = None
    venue_type = None
    c012s = []

    def finalize_current_piece():
        if not c012s:
            return

        # TODO: Filter dupes

        current_piece.copyright = c012s[2]
        assert len(c012s) == 3
        venue_name = c012s[1]

        current_piece.venue = get_venue(venue_name, venue_type)
        current_piece.study = study
        current_piece.save()

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

        if child.name == "br":
            continue

        if child.name == "div":
            div_class, = child["class"]
            p = child.p
            p_class, = p["class"]
            span = p.span
            span_class, = span["class"]
            text = child.get_text()

            key = (div_class, p_class, span_class)
            if key == ("c0", "c1", "c2"):
                c012s.append(text)
            elif key == ("c4", "c5", "c6"):
                current_piece.title = text
            elif key == ("c4", "c5", "c7"):
                match = C457_PARSE_RE.match(text)
                if match is None:
                    warn("c457 did not match expected format: '%s'"
                            % text[:20].encode("ascii", errors="replace"))
                    continue

                field = match.group(1)
                value = match.group(2)

                if field == "LENGTH":
                    continue
                elif field == "SECTION":
                    continue
                elif field == "BYLINE":
                    current_piece.byline = value
                elif field == "BYLINE":
                    current_piece.byline = value
                elif field == "LOAD-DATE":
                    current_piece.load_date = datetime.datetime.strptime(value, "%B %d, %Y").date()
                elif field == "LANGUAGE":
                    current_piece.language = value
                elif field == "PUBLICATION-TYPE":
                    venue_type = value
                elif field == "DOCUMENT-TYPE":
                    current_piece.document_type = value
                elif field == "DATELINE":
                    current_piece.dateline = value
                elif field == "URL":
                    current_piece.url = value
                elif field in ["GRAPHIC", "CORRECTION-DATE", "DISTRIBUTION", "JOURNAL-CODE"]:
                    # ignore for now
                    pass
                else:
                    raise RuntimeError("unknown c457 field: %s" % field)

            elif key == ("c3", "c1", "c2"):
                date_match = DATE_ISH_PARSE_RE.match(text)

                current_piece.pub_date_unparsed = text

                if date_match is None:
                    warn("c312 did not match expected date-ish format: '%s'"
                            % text[:20].encode("ascii", errors="replace"))
                else:
                    month = date_match.group(1)
                    day = date_match.group(2)
                    year = date_match.group(3)

                    rebuilt_pub_date = "%s %s, %s" % (month, day, year)
                    current_piece.pub_date = datetime.datetime.strptime(rebuilt_pub_date, "%B %d, %Y").date()

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
                print text
                raise RuntimeError(
                        "unknown doc key: %s" % str(key))

    finalize_current_piece()


if __name__ == "__main__":
    main()
