"""Evolution rules, and the version-group arithmetic that decides which ones a game gets."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.evolutions import evolution_encounters, evolution_rules
from livingdex_pipeline.models import EvolutionTrigger, Form, FormKind

RETRIEVED_ON = date(2026, 9, 21)

#: Where the version groups these tests use sit in the series, as PokeAPI orders them.
ORDER = {
    "red-blue": 1,
    "gold-silver": 3,
    "ruby-sapphire": 5,
    "emerald": 6,
    "diamond-pearl": 8,
    "black-white": 11,
    "sun-moon": 17,
}


def link(to: str, details: list[dict], evolves_to: list | None = None) -> dict:
    return {
        "species": {"name": to},
        "evolution_details": details,
        "evolves_to": evolves_to or [],
    }


def detail(trigger: str, version_group: str, **rest) -> dict:
    return {"trigger": {"name": trigger}, "version_group": {"name": version_group}, **rest}


class FakeApi:
    """Answers chain, version-group and name lookups out of a dict."""

    def __init__(
        self,
        chains: dict[str, dict],
        species: dict[str, str] | None = None,
        varieties: dict[str, list[tuple[str, bool]]] | None = None,
    ) -> None:
        self._chains = chains
        self._species = species or {}
        self._varieties = varieties or {}

    def retrieved_on(self, url: str) -> date:
        """The day the cache says this url was fetched, which a citation carries."""
        return RETRIEVED_ON

    def varieties(self, species: str, *, refresh: bool = False) -> list[tuple[str, bool]]:
        """Which Pokemon a species is. One, and it is the default, unless a test says otherwise.

        The default matters here rather than being scenery: it is how a form name that is really
        PokeAPI spelling out a default - ``lycanroc-midday`` - is told from one that is a second
        Pokemon, and a species with no second Pokemon can have neither.
        """
        return self._varieties.get(species, [(species, True)])

    def evolution_chain(self, species: str, *, refresh: bool = False) -> str:
        return self._species.get(species, next(iter(self._chains)))

    def resource(self, path: str, *, refresh: bool = False):
        if path.startswith("evolution-chain/"):
            return {"chain": self._chains[path.removeprefix("evolution-chain/")]}

        if path.startswith("version-group/"):
            return {"order": ORDER[path.removeprefix("version-group/")]}

        slug = path.rsplit("/", 1)[-1]
        return {"names": [{"language": {"name": "en"}, "name": slug.replace("-", " ").title()}]}


# --- the shared table -------------------------------------------------------------------------


def test_a_level_up_rule_carries_its_level() -> None:
    api = FakeApi(
        {
            "ralts": {
                "species": {"name": "ralts"},
                "evolves_to": [link("kirlia", [detail("level-up", "ruby-sapphire", min_level=20)])],
            }
        }
    )

    rule = evolution_rules(api, chains=["ralts"])[0]

    assert rule.id == "ralts-to-kirlia"
    assert rule.from_.species == "ralts"
    assert rule.to.species == "kirlia"
    assert rule.trigger is EvolutionTrigger.LEVEL_UP
    assert rule.conditions[0].level == 20


def test_a_trade_with_a_held_item_reads_as_both() -> None:
    api = FakeApi(
        {
            "horsea": {
                "species": {"name": "seadra"},
                "evolves_to": [
                    link(
                        "kingdra",
                        [
                            detail(
                                "trade",
                                "gold-silver",
                                held_item={"name": "dragon-scale"},
                            )
                        ],
                    )
                ],
            }
        }
    )

    rule = evolution_rules(api, chains=["horsea"])[0]

    assert rule.trigger is EvolutionTrigger.TRADE
    assert rule.conditions[0].item == "Dragon Scale"


def test_a_trigger_with_no_name_of_its_own_says_what_it_needs() -> None:
    api = FakeApi(
        {
            "nincada": {
                "species": {"name": "nincada"},
                "evolves_to": [link("shedinja", [detail("shed", "ruby-sapphire")])],
            }
        }
    )

    rule = evolution_rules(api, chains=["nincada"])[0]

    assert rule.trigger is EvolutionTrigger.OTHER
    assert "spare Poke Ball" in rule.conditions[0].description


def test_a_pair_with_two_variants_names_the_version_group_of_each() -> None:
    api = FakeApi(
        {
            "feebas": {
                "species": {"name": "feebas"},
                "evolves_to": [
                    link(
                        "milotic",
                        [
                            detail("level-up", "ruby-sapphire", min_beauty=170),
                            detail("trade", "black-white", held_item={"name": "prism-scale"}),
                        ],
                    )
                ],
            }
        }
    )

    ids = [rule.id for rule in evolution_rules(api, chains=["feebas"])]

    assert ids == ["feebas-to-milotic-ruby-sapphire", "feebas-to-milotic-black-white"]


def test_beauty_has_no_type_of_its_own_so_it_is_said_in_words() -> None:
    api = FakeApi(
        {
            "feebas": {
                "species": {"name": "feebas"},
                "evolves_to": [
                    link("milotic", [detail("level-up", "ruby-sapphire", min_beauty=170)])
                ],
            }
        }
    )

    rule = evolution_rules(api, chains=["feebas"])[0]

    assert rule.conditions[0].description == "with Beauty 170 or higher"


# --- what one game can use --------------------------------------------------------------------


def feebas_api() -> FakeApi:
    return FakeApi(
        {
            "feebas": {
                "species": {"name": "feebas"},
                "evolves_to": [
                    link(
                        "milotic",
                        [
                            detail("level-up", "ruby-sapphire", min_beauty=170),
                            detail("trade", "black-white", held_item={"name": "prism-scale"}),
                        ],
                    )
                ],
            }
        },
        species={"feebas": "feebas", "milotic": "feebas"},
    )


def test_a_game_gets_the_newest_variant_it_is_old_enough_for() -> None:
    methods = evolution_encounters(
        feebas_api(),
        game_id="emerald",
        version_group="emerald",
        species=["feebas", "milotic"],
    )

    # Emerald came before Black and White, so it evolves Feebas the way its own generation did.
    assert [one.rule for one in methods] == ["feebas-to-milotic-ruby-sapphire"]
    assert methods[0].target.species == "milotic"


def test_a_later_game_gets_the_variant_that_replaced_it() -> None:
    methods = evolution_encounters(
        feebas_api(),
        game_id="black",
        version_group="black-white",
        species=["feebas", "milotic"],
    )

    assert [one.rule for one in methods] == ["feebas-to-milotic-black-white"]


def test_an_evolution_from_a_later_generation_is_not_offered() -> None:
    api = FakeApi(
        {
            "roselia": {
                "species": {"name": "roselia"},
                "evolves_to": [
                    link(
                        "roserade",
                        [detail("use-item", "diamond-pearl", item={"name": "shiny-stone"})],
                    )
                ],
            }
        },
        species={"roselia": "roselia"},
    )

    assert (
        evolution_encounters(
            api,
            game_id="emerald",
            version_group="emerald",
            species=["roselia"],
        )
        == []
    )


def test_a_species_the_game_does_not_have_evolves_into_nothing_here() -> None:
    api = FakeApi(
        {
            "ralts": {
                "species": {"name": "ralts"},
                "evolves_to": [link("kirlia", [detail("level-up", "ruby-sapphire", min_level=20)])],
            }
        },
        species={"kirlia": "ralts"},
    )

    # Kirlia is asked about, Ralts is not: nothing in this game turns into a Kirlia.
    assert (
        evolution_encounters(
            api,
            game_id="emerald",
            version_group="emerald",
            species=["kirlia"],
        )
        == []
    )


# --- forms: which Pokemon a way of evolving produces ------------------------------------------


def form(form_id: str, species: str, *games: str) -> Form:
    return Form(id=form_id, species=species, name=form_id, kind=FormKind.REGIONAL, games=games)


def lycanroc_api() -> FakeApi:
    """Rockruff's three Lycanroc, which all start in the same version group.

    The shape that made this worth writing: they are not one way replacing another, they are
    three ways that arrived together, and picking the newest picks all three.
    """
    return FakeApi(
        {
            "rockruff": {
                "species": {"name": "rockruff"},
                "evolves_to": [
                    link(
                        "lycanroc",
                        [
                            detail(
                                "level-up",
                                "sun-moon",
                                min_level=25,
                                time_of_day="day",
                                evolved_pokemon_form={"name": "lycanroc-midday"},
                            ),
                            detail(
                                "level-up",
                                "sun-moon",
                                min_level=25,
                                time_of_day="night",
                                evolved_pokemon_form={"name": "lycanroc-midnight"},
                            ),
                            detail(
                                "level-up",
                                "sun-moon",
                                min_level=25,
                                required_pokemon_form={"name": "rockruff-own-tempo"},
                                evolved_pokemon_form={"name": "lycanroc-dusk"},
                            ),
                        ],
                    )
                ],
            }
        },
        varieties={
            "lycanroc": [
                ("lycanroc", True),
                ("lycanroc-midnight", False),
                ("lycanroc-dusk", False),
            ],
            "rockruff": [("rockruff", True), ("rockruff-own-tempo", False)],
        },
    )


def test_ways_that_start_together_are_all_kept() -> None:
    """One replaces another only when it is newer. Three at once are three evolutions."""
    methods = evolution_encounters(
        lycanroc_api(),
        game_id="ultra-sun",
        version_group="sun-moon",
        species=["rockruff", "lycanroc"],
        forms=[
            form("lycanroc-midnight", "lycanroc", "ultra-sun"),
            form("lycanroc-dusk", "lycanroc", "ultra-sun"),
            form("rockruff-own-tempo", "rockruff", "ultra-sun"),
        ],
        all_forms=[
            form("lycanroc-midnight", "lycanroc", "ultra-sun"),
            form("lycanroc-dusk", "lycanroc", "ultra-sun"),
            form("rockruff-own-tempo", "rockruff", "ultra-sun"),
        ],
    )

    assert [one.target.form for one in methods] == [
        None,
        "lycanroc-midnight",
        "lycanroc-dusk",
    ]


def test_a_form_another_game_has_is_not_a_way_here() -> None:
    """Sun reads Ultra Sun's chain and must not be told to do what only Ultra Sun can."""
    forms = [
        form("lycanroc-midnight", "lycanroc", "sun", "ultra-sun"),
        form("lycanroc-dusk", "lycanroc", "ultra-sun"),
        form("rockruff-own-tempo", "rockruff", "ultra-sun"),
    ]

    methods = evolution_encounters(
        lycanroc_api(),
        game_id="sun",
        version_group="sun-moon",
        species=["rockruff", "lycanroc"],
        forms=[one for one in forms if "sun" in one.games],
        all_forms=forms,
    )

    assert [one.target.form for one in methods] == [None, "lycanroc-midnight"]


def test_a_game_with_no_form_table_reads_as_it_always_did() -> None:
    """Every fork lands on the species, and the three of them are one record rather than three.

    The case a game written before any of this has to keep working in: no forms passed, so
    nothing can be told apart, and what comes out is the single Lycanroc record that came out
    before. ``lycanroc-midday`` does not become a form on its own account either - it is
    PokeAPI's name for the default, which is the species.
    """
    methods = evolution_encounters(
        lycanroc_api(),
        game_id="sun",
        version_group="sun-moon",
        species=["rockruff", "lycanroc"],
    )

    assert len(methods) == 1
    assert methods[0].target.species == "lycanroc"
    assert methods[0].target.form is None


def test_a_rule_names_the_form_it_produces() -> None:
    rules = evolution_rules(
        lycanroc_api(),
        chains=["rockruff"],
        forms=[
            form("lycanroc-midnight", "lycanroc", "sun"),
            form("lycanroc-dusk", "lycanroc", "ultra-sun"),
            form("rockruff-own-tempo", "rockruff", "ultra-sun"),
        ],
    )

    by_id = {one.id: one for one in rules}

    assert by_id["rockruff-to-lycanroc-midnight"].to.form == "lycanroc-midnight"
    assert by_id["rockruff-to-lycanroc-dusk"].from_.form == "rockruff-own-tempo"
    # The one whose form is PokeAPI spelling out a default keeps the plain id and no form.
    assert by_id["rockruff-to-lycanroc"].to.form is None


def shellos_api() -> FakeApi:
    """Shellos's two seas, which are one Pokemon wearing two forms.

    The other shape, and the one that made the first attempt at this wrong. A Midnight Lycanroc
    is a second Pokemon; an East Sea Shellos is not, and PokeAPI gives the ordinary one a form
    name too - ``shellos-west``. So "is it another Pokemon" cannot be the whole test, and
    neither can "does the name look like a form".
    """
    return FakeApi(
        {
            "shellos": {
                "species": {"name": "shellos"},
                "evolves_to": [
                    link(
                        "gastrodon",
                        [
                            detail(
                                "level-up",
                                "diamond-pearl",
                                min_level=30,
                                required_pokemon_form={"name": "shellos-west"},
                                evolved_pokemon_form={"name": "gastrodon-west"},
                            ),
                            detail(
                                "level-up",
                                "diamond-pearl",
                                min_level=30,
                                required_pokemon_form={"name": "shellos-east"},
                                evolved_pokemon_form={"name": "gastrodon-east"},
                            ),
                        ],
                    )
                ],
            }
        }
    )


def test_a_form_with_no_pokemon_of_its_own_is_still_a_form() -> None:
    """Both seas, and the West one under the species it is the default of."""
    forms = [
        form("shellos-east", "shellos", "diamond"),
        form("gastrodon-east", "gastrodon", "diamond"),
    ]

    methods = evolution_encounters(
        shellos_api(),
        game_id="diamond",
        version_group="diamond-pearl",
        species=["shellos", "gastrodon"],
        forms=forms,
        all_forms=forms,
    )

    assert [one.target.form for one in methods] == [None, "gastrodon-east"]
