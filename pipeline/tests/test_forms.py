"""The shared forms table: which face of a species is an entry of its own, and where."""

from __future__ import annotations

import pytest

from livingdex_pipeline.forms import FORMS_NAMED_BY_THE_GAME, FormsError, form_table
from livingdex_pipeline.models import FormKind, PokemonType, Species

#: Three version groups is enough to show every rule: one before the form arrives, the one it
#: arrives in, and one after. Their generations are what keeps a species out of a game older
#: than it is.
GROUPS = {
    "gold-silver": (3, ["gold", "silver"], 2),
    "diamond-pearl": (8, ["diamond", "pearl"], 4),
    "platinum": (9, ["platinum"], 4),
    "sword-shield": (20, ["sword"], 8),
    # After all of them, and holding 153 species: the pair no version group can speak for.
    "lets-go-pikachu-lets-go-eevee": (19, ["lets-go-pikachu", "lets-go-eevee"], 7),
}


def species(name: str, *, types=("normal",)) -> Species:
    return Species(
        id=name,
        national_dex_number=1,
        name=name.title(),
        types=[PokemonType(one) for one in types],
        evolution_chain=name,
    )


class FakeApi:
    """PokeAPI's four form endpoints and nothing else.

    ``varieties`` is species -> the Pokemon under it, ``forms`` is Pokemon -> the faces under
    that, which is the two shapes the real source uses.
    """

    def __init__(
        self,
        *,
        varieties: dict[str, list[str]],
        forms: dict[str, list[str]],
        pokemon: dict[str, dict],
        form_data: dict[str, dict],
        generation: dict[str, int] | None = None,
        gendered: set[str] | None = None,
    ) -> None:
        self._varieties = varieties
        self._forms = forms
        self._pokemon = pokemon
        self._forms_raw = form_data
        self._generation = generation or {}
        self._gendered = gendered or set()

    def resource(self, path: str, *, refresh: bool = False):
        if path.startswith("version-group?"):
            return {"results": [{"name": name} for name in GROUPS]}

        if path.startswith("version-group/"):
            order, versions, generation = GROUPS[path.removeprefix("version-group/")]
            return {
                "order": order,
                "versions": [{"name": one} for one in versions],
                "generation": {"url": f"https://pokeapi.co/api/v2/generation/{generation}/"},
            }

        if path.startswith("pokemon-species/"):
            name = path.removeprefix("pokemon-species/")
            varieties = self._varieties.get(name, [])
            return {
                "id": 1,
                "varieties": [
                    {"is_default": index == 0, "pokemon": {"name": one}}
                    for index, one in enumerate(varieties)
                ],
                "has_gender_differences": name in self._gendered,
                "generation": {
                    "url": (
                        f"https://pokeapi.co/api/v2/generation/{self._generation.get(name, 2)}/"
                    )
                },
            }

        if path.startswith("pokemon-form/"):
            return self._forms_raw[path.removeprefix("pokemon-form/")]

        name = path.removeprefix("pokemon/")
        return {
            "name": name,
            "forms": [{"name": one} for one in self._forms[name]],
            **self._pokemon[name],
        }


def pokemon(*, types=("normal",), attack: int = 50, abilities=("run-away",)) -> dict:
    return {
        "id": 1,
        "types": [{"slot": i, "type": {"name": one}} for i, one in enumerate(types, start=1)],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 50},
            {"stat": {"name": "attack"}, "base_stat": attack},
        ],
        "abilities": [{"ability": {"name": one}} for one in abilities],
    }


def form(
    *,
    name: str,
    group: str = "gold-silver",
    default: bool = False,
    battle_only: bool = False,
    mega: bool = False,
    types=None,
) -> dict:
    return {
        "form_name": name,
        "is_default": default,
        "is_battle_only": battle_only,
        "is_mega": mega,
        "version_group": {"name": group},
        "types": [{"slot": i, "type": {"name": one}} for i, one in enumerate(types or [], 1)],
        "sprites": {"front_default": f"https://sprites/1-{name}.png" if name else None},
    }


GAMES = ["gold", "silver", "diamond", "pearl", "platinum"]


def build(api: FakeApi, *one: Species):
    """The table's forms, which is what most of these are about."""
    return form_table(api, species=list(one), game_ids=GAMES).forms


# --- one Pokemon wearing several faces ----------------------------------------------------------


def unown_api() -> FakeApi:
    return FakeApi(
        varieties={"unown": ["unown"]},
        forms={"unown": ["unown-a", "unown-b", "unown-exclamation"]},
        pokemon={"unown": pokemon(types=("psychic",))},
        form_data={
            "unown-a": form(name="a", default=True),
            "unown-b": form(name="b"),
            "unown-exclamation": form(name="exclamation", group="diamond-pearl"),
        },
    )


def test_the_face_a_species_wears_by_default_is_not_a_form_of_itself() -> None:
    # The app draws a line for the species and then its forms under it, so counting the default
    # face as a form would put Unown A twice on the same row.
    found = build(unown_api(), species("unown", types=("psychic",)))

    assert [one.id for one in found] == ["unown-b", "unown-exclamation"]


def test_one_pokemon_with_several_faces_is_cosmetic() -> None:
    # Measured rather than listed: Unown's letters share a Pokemon, so there is nothing to
    # differ in. That is the whole difference between a letter and a cloak.
    [letter, _] = build(unown_api(), species("unown", types=("psychic",)))

    assert letter.kind is FormKind.COSMETIC
    assert letter.name == "B"
    # The species' own typing, so the record says nothing about it.
    assert letter.types is None


def test_a_form_reaches_every_game_from_the_one_it_arrived_in() -> None:
    letter, added_later = build(unown_api(), species("unown", types=("psychic",)))

    assert letter.games == ["diamond", "gold", "pearl", "platinum", "silver"]
    # And one that arrived two generations later does not reach backwards.
    assert added_later.games == ["diamond", "pearl", "platinum"]


def test_a_slug_that_reads_badly_is_given_a_name() -> None:
    # The app prints "Unown (!)", so the label is the part in brackets. "Exclamation" is what
    # the source calls it and not what the game ever showed anyone.
    [_, punctuation] = build(unown_api(), species("unown", types=("psychic",)))

    assert punctuation.name == "!"


# --- several Pokemon under one species ----------------------------------------------------------


def wormadam_api(**kwargs) -> FakeApi:
    return FakeApi(
        varieties={"wormadam": ["wormadam-plant", "wormadam-trash"]},
        forms={"wormadam-plant": ["wormadam-plant"], "wormadam-trash": ["wormadam-trash"]},
        pokemon={
            "wormadam-plant": pokemon(types=("bug", "grass")),
            "wormadam-trash": pokemon(types=("bug", "steel")),
        },
        form_data={
            "wormadam-plant": form(name="plant", default=True, group="diamond-pearl"),
            "wormadam-trash": form(name="trash", default=True, group="diamond-pearl"),
        },
        generation={"wormadam": 4},
        **kwargs,
    )


def test_a_form_typed_differently_from_its_species_is_functional() -> None:
    [trash] = build(wormadam_api(), species("wormadam", types=("bug", "grass")))

    assert trash.kind is FormKind.FUNCTIONAL
    assert trash.name == "Trash"
    # Carried on the record, because it is not the species' typing any more.
    assert trash.types == [PokemonType.BUG, PokemonType.STEEL]


def test_a_form_that_differs_only_in_its_abilities_is_still_functional() -> None:
    # Basculin's two stripes are the same typing and the same stats, and one of them has Rock
    # Head where the other has Adaptability. A player raising it knows the difference.
    api = FakeApi(
        varieties={"basculin": ["basculin-red-striped", "basculin-blue-striped"]},
        forms={
            "basculin-red-striped": ["basculin-red-striped"],
            "basculin-blue-striped": ["basculin-blue-striped"],
        },
        pokemon={
            "basculin-red-striped": pokemon(types=("water",), abilities=("adaptability",)),
            "basculin-blue-striped": pokemon(types=("water",), abilities=("rock-head",)),
        },
        form_data={
            "basculin-red-striped": form(name="red-striped", default=True),
            "basculin-blue-striped": form(name="blue-striped", default=True),
        },
    )

    [blue] = build(api, species("basculin", types=("water",)))

    assert blue.kind is FormKind.FUNCTIONAL
    assert blue.types is None


# --- what is left out -------------------------------------------------------------------------


def test_a_form_that_lasts_until_the_battle_ends_is_not_an_entry() -> None:
    # Castform's weather, Darmanitan's Zen Mode, Meloetta's Pirouette. A living dex is a box of
    # Pokemon, and none of these survives being put in one.
    api = FakeApi(
        varieties={"castform": ["castform", "castform-sunny"]},
        forms={"castform": ["castform"], "castform-sunny": ["castform-sunny"]},
        pokemon={"castform": pokemon(), "castform-sunny": pokemon(types=("fire",))},
        form_data={
            "castform": form(name="", default=True),
            "castform-sunny": form(name="sunny", default=True, battle_only=True),
        },
    )

    assert build(api, species("castform")) == []


def test_a_form_that_is_only_an_item_being_held_is_not_an_entry() -> None:
    # Arceus's plates and Genesect's drives. Take the item off and it is the same Pokemon, so
    # an entry each would ask a player to catch one Arceus eighteen times.
    api = FakeApi(
        varieties={"arceus": ["arceus"]},
        forms={"arceus": ["arceus-normal", "arceus-fire"]},
        pokemon={"arceus": pokemon()},
        form_data={
            "arceus-normal": form(name="normal", default=True, group="diamond-pearl"),
            "arceus-fire": form(name="fire", group="diamond-pearl", types=["fire"]),
        },
        generation={"arceus": 4},
    )

    assert build(api, species("arceus")) == []


def test_a_form_that_arrived_after_the_newest_game_here_is_left_out() -> None:
    # Every Mega, Gigantamax and regional form of a species this dataset holds falls out this
    # way, without a list of them to keep up to date.
    api = FakeApi(
        varieties={"lopunny": ["lopunny", "lopunny-mega"]},
        forms={"lopunny": ["lopunny"], "lopunny-mega": ["lopunny-mega"]},
        pokemon={"lopunny": pokemon(), "lopunny-mega": pokemon(types=("fighting",))},
        form_data={
            "lopunny": form(name="", default=True, group="diamond-pearl"),
            "lopunny-mega": form(name="mega", group="sword-shield"),
        },
        generation={"lopunny": 4},
    )

    assert build(api, species("lopunny")) == []


def test_a_species_no_game_here_can_hold_is_not_asked_about_at_all() -> None:
    # The species table reaches every generation and this dataset stops well short of it, so
    # most of what would be fetched is a form of something nobody here has.
    api = FakeApi(
        varieties={},
        forms={},
        pokemon={},
        form_data={},
        generation={"pyroar": 6},
        gendered={"pyroar"},
    )

    assert build(api, species("pyroar")) == []


# --- the gender flag ----------------------------------------------------------------------------


def test_a_species_whose_sexes_are_drawn_apart_gets_one_entry_for_the_other_half() -> None:
    # No form anywhere in the source - a boolean and two sprites - and the entry only belongs
    # to games old enough to draw the difference at all.
    api = FakeApi(
        varieties={"venusaur": ["venusaur"]},
        forms={"venusaur": ["venusaur"]},
        pokemon={"venusaur": pokemon()},
        form_data={"venusaur": form(name="", default=True)},
        generation={"venusaur": 1},
        gendered={"venusaur"},
    )

    [female] = build(api, species("venusaur"))

    assert female.id == "venusaur-female"
    assert female.name == "Female"
    assert female.kind is FormKind.GENDER
    # Nothing before Generation 4 drew a female Venusaur any differently.
    assert female.games == ["diamond", "pearl", "platinum"]


def test_the_two_species_that_do_have_a_gender_form_are_not_given_a_second_one() -> None:
    # Frillish and Jellicent are the only ones the source models as forms rather than as a
    # flag, and they carry the flag too.
    api = wormadam_api(gendered={"wormadam"})
    api._forms_raw["wormadam-trash"] = form(name="female", default=True, group="diamond-pearl")

    found = build(api, species("wormadam", types=("bug", "grass")))

    assert [one.kind for one in found] == [FormKind.GENDER]
    assert [one.id for one in found] == ["wormadam-trash"]


def test_the_games_that_hold_a_list_are_left_out_of_a_table_that_cannot_speak_for_them() -> None:
    # Wormadam's cloaks arrive in Diamond and Pearl, so every later game that can hold anything
    # up to its own National Dex number has them - Platinum does. Let's Go and Sword and Shield
    # cannot: their boxes hold a list instead, and the first build that registered the Let's Go
    # pair put 578 lines into the form table this way, almost none of them true.
    [trash] = form_table(
        wormadam_api(),
        species=[species("wormadam", types=("bug", "grass"))],
        game_ids=[*GAMES, "sword", "lets-go-pikachu", "lets-go-eevee"],
    ).forms

    assert "platinum" in trash.games
    assert "sword" not in trash.games
    assert "lets-go-pikachu" not in trash.games
    assert "lets-go-eevee" not in trash.games


def test_a_form_that_belongs_to_nothing_but_that_pair_is_left_out_altogether() -> None:
    # Which is the partner Pikachu's shape: it arrived in that version group and exists
    # nowhere else, so until step 8 names it by hand the table has no room for it.
    api = wormadam_api()
    api._forms_raw["wormadam-trash"] = form(
        name="trash", default=True, group="lets-go-pikachu-lets-go-eevee"
    )

    found = form_table(
        api,
        species=[species("wormadam", types=("bug", "grass"))],
        game_ids=[*GAMES, "lets-go-pikachu"],
    ).forms

    assert found == []

    # Three pairs now, for three different reasons, and the third is the one that shows what the
    # rule actually reads. Let's Go and Galar hold a list instead of a number; Brilliant Diamond
    # and Shining Pearl hold everything up to 493 and the rule was wrong about them anyway,
    # because all it asks is when a form arrived and these came out last.
    assert set(FORMS_NAMED_BY_THE_GAME) == {
        "lets-go-pikachu",
        "lets-go-eevee",
        "sword",
        "shield",
        "brilliant-diamond",
        "shining-pearl",
    }


# --- what the source cannot say -----------------------------------------------------------------


def test_a_face_of_one_pokemon_is_filed_under_the_name_the_source_uses() -> None:
    # A sprite sheet keeps Unown's letters as "201-b.png", which is the file name the source's
    # own address for the form already ends in. Guessing it would be guessing at a convention
    # nobody wrote down.
    table = form_table(unown_api(), species=[species("unown")], game_ids=GAMES)

    assert table.pictures["unown-b"] == ("1-b.png",)


def test_a_variety_is_filed_under_its_own_number_and_its_name() -> None:
    # A variety is a Pokemon with a number of its own - Wash Rotom is 10009 - and the sheets
    # are not consistent about which of the two they use, so both are offered in order.
    api = wormadam_api()
    api._pokemon["wormadam-trash"]["id"] = 10005

    table = form_table(api, species=[species("wormadam", types=("bug", "grass"))], game_ids=GAMES)

    assert table.pictures["wormadam-trash"] == ("10005.png", "1-trash.png")


def test_the_gender_flag_is_filed_in_the_folder_a_sheet_keeps_its_females_in() -> None:
    api = FakeApi(
        varieties={"venusaur": ["venusaur"]},
        forms={"venusaur": ["venusaur"]},
        pokemon={"venusaur": pokemon()},
        form_data={"venusaur": form(name="", default=True)},
        generation={"venusaur": 1},
        gendered={"venusaur"},
    )

    table = form_table(api, species=[species("venusaur")], game_ids=GAMES)

    assert table.pictures["venusaur-female"] == ("female/1.png",)


def test_a_form_the_version_group_cannot_place_is_written_out_by_hand() -> None:
    # Deoxys is the awkward case twice over. Three Generation 3 cartridges each hold it in a
    # different forme and the source can only name the version group, which pairs FireRed and
    # LeafGreen together - and from Generation 4 on a meteorite changes it at will, so all three
    # formes belong to every game that has one. Pinning them to the cartridge they came from was
    # right while the dataset stopped at Generation 3 and wrong from Diamond onwards.
    from livingdex_pipeline import forms as module

    assert module.ONLY_IN["deoxys-attack"][0] == "firered"
    assert module.ONLY_IN["deoxys-defense"][0] == "leafgreen"
    assert module.ONLY_IN["deoxys-speed"][0] == "emerald"
    for one in ("deoxys-attack", "deoxys-defense", "deoxys-speed"):
        assert set(module.ONLY_IN[one]) - {"firered", "leafgreen", "emerald"} == set(
            module.METEORITE
        )

    # Ruby and Sapphire have no meteorite and no forme but the one they hold, so they are not on
    # the list; the spiky-eared Pichu is the other kind of hand-written answer, a form that
    # cannot leave the game it is in.
    assert "ruby" not in module.METEORITE
    assert module.ONLY_IN["pichu-spiky-eared"] == ("heartgold", "soulsilver")

    # And every generation since keeps putting one somewhere. Alola's is beside Sophocles in the
    # Hokulani Observatory, which is the sort of thing a version group can never say.
    assert {"sun", "moon"} <= set(module.METEORITE)


def test_a_game_the_source_has_never_heard_of_fails_the_build() -> None:
    # A game id that is not also PokeAPI's name for that version would otherwise lose every
    # form it should have, silently.
    api = unown_api()

    with pytest.raises(FormsError, match="version group"):
        form_table(api, species=[species("unown")], game_ids=["gold", "shining-pearl"])


def test_the_table_comes_back_in_the_order_it_will_be_read_back_in() -> None:
    # A game writes its form records in the order the table hands them over, and the table comes
    # from memory on a full build and off disk on a single-game one. Those two orders were
    # different for a while, so the same game built two ways wrote the same records twice in two
    # orders and the committed dataset had a 352-line diff with nothing in it.
    api = unown_api()

    found = form_table(api, species=[species("unown")], game_ids=GAMES).forms

    assert [one.id for one in found] == sorted(one.id for one in found)
