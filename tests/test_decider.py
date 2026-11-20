"""Regression tests for decider.decide(): one case per mistake we found and fixed (see docs/poster_facts.md, section 7).
Developed with AI assistance (Claude); the rules under test are Ekam's."""
import pytest

from decider import decide


@pytest.mark.parametrize("a, b, expected", [
    # one distinctive word differs -> different institutions (found by the audit)
    ("Ohio State University", "Iowa State University", "unrelated"),
    ("Swiss National Science Foundation", "US National Science Foundation", "unrelated"),
    ("City of Grande Prairie", "County of Grande Prairie", "unrelated"),
    # one word differs by a typo or spelling variant -> still the same institution
    ("Woods Hole Oceanographic Insitution", "Woods Hole Oceanographic Institution", "duplicate"),
    ("World Meteorological Organisation, Global Atmosphere Watch", "World Meteorological Organization, Global Atmosphere Watch", "duplicate"),
    # the extra word names a part of the other name -> hierarchy, not duplicate
    ("Cornell University Library", "Cornell University", "hierarchy"),
    ("University of Maryland Libraries", "University of Maryland", "hierarchy"),
    ("Stockholm University Press", "Stockholm University", "hierarchy"),
    # the extra word is harmless -> duplicate
    ("RWTH Aachen", "RWTH Aachen University", "duplicate"),
    # basics
    ("Purdue University", "Harvard University", "unrelated"),
    ("Cornell University", "Cornell University, Roper Center", "hierarchy"),
    ("Science & Technology Council", "Science and Technology Council", "duplicate"),
])
def test_decide(a, b, expected):
    assert decide(a, b) == expected
    assert decide(b, a) == expected      # the answer must not depend on the order of the two names
