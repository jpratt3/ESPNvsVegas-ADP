"""Name normalization is the join key between four sources that spell players
differently. If it drifts, rows stop matching and players silently lose their lines
rather than failing loudly, so the rules are pinned here."""

import unittest

from app.matching import ALIASES, normalize


class TestNormalize(unittest.TestCase):
    def test_case_and_punctuation_are_stripped(self):
        self.assertEqual(normalize("Ja'Marr Chase"), "jamarr chase")
        self.assertEqual(normalize("JA'MARR CHASE"), "jamarr chase")
        self.assertEqual(normalize("De'Von Achane"), "devon achane")

    def test_hyphens_and_periods_become_spaces_or_vanish(self):
        self.assertEqual(normalize("Amon-Ra St. Brown"), "amonra st brown")
        self.assertEqual(normalize("T.J. Hockenson"), "tj hockenson")

    def test_accents_are_folded(self):
        self.assertEqual(normalize("Aristótelis Peña"), "aristotelis pena")

    def test_generational_suffixes_are_dropped(self):
        # Books and ESPN disagree about whether to print the suffix at all.
        self.assertEqual(normalize("Michael Pittman Jr."), "michael pittman")
        self.assertEqual(normalize("Michael Pittman"), "michael pittman")
        self.assertEqual(normalize("Odell Beckham Jr"), "odell beckham")

    def test_the_lll_typo_is_treated_as_a_suffix(self):
        # At least one book prints "III" as three lowercase L's.
        self.assertEqual(normalize("Marvin Harrison lll"), "marvin harrison")
        self.assertEqual(normalize("Marvin Harrison III"), "marvin harrison")

    def test_aliases_resolve_to_the_canonical_name(self):
        self.assertEqual(normalize("Hollywood Brown"), "marquise brown")
        self.assertEqual(normalize("Gabriel Davis"), "gabe davis")
        self.assertEqual(normalize("Cam Ward"), "cameron ward")

    def test_the_bryce_hall_alias_points_at_the_running_back(self):
        # A book posted 5.5 rushing TDs under "Bryce Hall", who is a cornerback.
        # The line belongs to Breece Hall; without this the RB loses the stat.
        self.assertEqual(normalize("Bryce Hall"), "breece hall")

    def test_sources_spelling_a_player_differently_still_join(self):
        for a, b in [
            ("Gabriel Davis", "Gabe Davis"),
            ("Joshua Palmer", "Josh Palmer"),
            ("Cameron Skattebo", "Cam Skattebo"),
            ("Michael Pittman Jr.", "MICHAEL PITTMAN"),
        ]:
            self.assertEqual(normalize(a), normalize(b), f"{a!r} and {b!r} did not join")

    def test_normalize_is_idempotent(self):
        # The output is used as a dict key and is sometimes re-normalized on the way
        # through. A second pass must be a no-op, which also means no alias may map
        # onto another alias's key.
        samples = [
            "Ja'Marr Chase", "Amon-Ra St. Brown", "Hollywood Brown", "Bryce Hall",
            "Marvin Harrison lll", "Michael Pittman Jr.", "Cam Ward",
        ]
        for name in samples:
            once = normalize(name)
            self.assertEqual(normalize(once), once, f"not idempotent for {name!r}")

    def test_no_alias_target_is_itself_an_alias_key(self):
        # Guards the idempotence property above against a future edit.
        for src, dst in ALIASES.items():
            self.assertNotIn(dst, ALIASES, f"{src!r} -> {dst!r} chains to another alias")

    def test_alias_keys_are_stored_already_normalized(self):
        # ALIASES is consulted with an already-normalized string, so a key that is not
        # itself normalized could never match and would be dead config.
        for key in ALIASES:
            stripped = key.lower()
            self.assertEqual(key, stripped, f"alias key {key!r} is not lowercase")
            self.assertNotIn(".", key, f"alias key {key!r} contains punctuation")

    def test_empty_and_whitespace_are_handled(self):
        self.assertEqual(normalize(""), "")
        self.assertEqual(normalize("   "), "")
