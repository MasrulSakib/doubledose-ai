"""Conservative ingredient-name normalisation for overlap comparison.

Two records describe the same active moiety when they differ only by
whitespace, a spelling variant, or a trailing salt/hydrate word
("Amoxicillin" / "Amoxicillin Trihydrate", "Diclofenac Sodium" /
"Diclofenac Potassium"). Bare minerals are never reduced to the element,
so "Calcium Acetate" and "Zinc Sulfate" keep their full names.
"""

import re
import unicodedata

SALT_TOKENS = frozenset(
    {
        "hydrochloride", "dihydrochloride", "hcl", "hydrobromide", "bromide",
        "chloride", "sodium", "disodium", "potassium", "calcium", "magnesium",
        "sulfate", "phosphate", "acetate", "citrate", "maleate", "besilate",
        "mesylate", "tartrate", "succinate", "fumarate", "hydrate",
        "monohydrate", "dihydrate", "trihydrate", "hemihydrate", "anhydrous",
    }
)

# Stripping salt words from these would leave only an element or cation.
PROTECTED_BASES = frozenset(
    {
        "calcium", "sodium", "potassium", "magnesium", "zinc", "ferrous",
        "ferric", "iron", "lithium", "aluminium", "aluminum", "copper",
        "manganese",
    }
)

SPELLING_VARIANTS = {
    "sulphate": "sulfate",
    "besylate": "besilate",
    "polymixin": "polymyxin",
}


def normalize_ingredient_name(name: str) -> str:
    """Fold case, Unicode spaces (e.g. non-breaking) and known spellings."""
    text = unicodedata.normalize("NFKC", name).casefold()
    tokens = re.sub(r"\s+", " ", text).strip().split(" ")
    return " ".join(SPELLING_VARIANTS.get(token, token) for token in tokens if token)


def canonical_ingredient_key(name: str) -> str:
    """Key shared by records that name the same active moiety."""
    tokens = normalize_ingredient_name(name).split(" ")

    while (
        len(tokens) > 1
        and tokens[-1] in SALT_TOKENS
        and " ".join(tokens[:-1]) not in PROTECTED_BASES
    ):
        tokens.pop()

    return " ".join(tokens)
