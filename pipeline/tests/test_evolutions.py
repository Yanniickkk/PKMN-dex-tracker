"""Evolution rules, and the version-group arithmetic that decides which ones a game gets."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.evolutions import (
    NOT_IN_THE_SOURCE,
    evolution_encounters,
    evolution_rules,
)
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
    "lets-go-pikachu-lets-go-eevee": 21,
    "sword-shield": 22,
    "legends-arceus": 24,
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
            # Roserade is asked about too, or this would be refused for not being one of the
            # species this game holds and the version group would never be reached.
            species=["roselia", "roserade"],
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


def test_what_this_game_cannot_hold_is_no_way_to_get_anything_here() -> None:
    # Eevee is in the Let's Go pair's 153 and Espeon is not, and those boxes hold the list and
    # nothing else. Every game before them holds everything up to a number, so what a species
    # in the living dex evolves into was always in it too.
    api = FakeApi(
        {
            "eevee": {
                "species": {"name": "eevee"},
                "evolves_to": [
                    link("espeon", [detail("level-up", "gold-silver", min_happiness=160)])
                ],
            }
        },
        species={"eevee": "eevee", "espeon": "eevee"},
    )

    assert (
        evolution_encounters(
            api,
            game_id="lets-go-eevee",
            version_group="lets-go-pikachu-lets-go-eevee",
            species=["eevee"],
        )
        == []
    )


def test_a_game_can_name_an_evolution_the_chain_credits_it_with_and_it_has_not() -> None:
    # A chain has no column for where its rule can be used. Meltan becomes Melmetal on 400
    # Meltan Candy and that happens in Pokemon GO; the Let's Go pair receives the result through
    # the GO Park and cannot do it. The same shape as a gift the source files under the wrong
    # version, and named by the game rather than guessed at here.
    api = FakeApi(
        {
            "meltan": {
                "species": {"name": "meltan"},
                "evolves_to": [link("melmetal", [detail("use-item", "sun-moon")])],
            }
        },
        species={"meltan": "meltan", "melmetal": "meltan"},
    )

    def built(excluded: dict[str, str] | None) -> list:
        return evolution_encounters(
            api,
            game_id="lets-go-pikachu",
            version_group="lets-go-pikachu-lets-go-eevee",
            species=["meltan", "melmetal"],
            excluded=excluded,
        )

    assert [one.target.species for one in built(None)] == ["melmetal"]
    assert built({"melmetal": "400 Meltan Candy in Pokemon GO"}) == []


def raichu_api() -> FakeApi:
    """One Thunder Stone, two things it has made of a Pikachu, twenty-two years apart."""
    return FakeApi(
        {
            "pikachu": {
                "species": {"name": "pikachu"},
                "evolves_to": [
                    link(
                        "raichu",
                        [
                            detail("use-item", "red-blue", item={"name": "thunder-stone"}),
                            detail(
                                "use-item",
                                "sun-moon",
                                item={"name": "thunder-stone"},
                                evolved_pokemon_form={"name": "raichu-alola"},
                            ),
                        ],
                    )
                ],
            }
        },
        species={"pikachu": "pikachu", "raichu": "pikachu"},
        varieties={"raichu": [("raichu", True), ("raichu-alola", False)]},
    )


def rattata_api() -> FakeApi:
    """Generation 7 added a second Rattata rather than changing the first.

    The source says so: the newer detail requires ``rattata-alola`` and produces
    ``raticate-alola``, where the older requires nothing and produces the species.
    """
    return FakeApi(
        {
            "rattata": {
                "species": {"name": "rattata"},
                "evolves_to": [
                    link(
                        "raticate",
                        [
                            detail("level-up", "red-blue", min_level=20),
                            detail(
                                "level-up",
                                "sun-moon",
                                min_level=20,
                                required_pokemon_form={"name": "rattata-alola"},
                                evolved_pokemon_form={"name": "raticate-alola"},
                            ),
                        ],
                    )
                ],
            }
        },
        species={"rattata": "rattata", "raticate": "rattata"},
        varieties={
            "rattata": [("rattata", True), ("rattata-alola", False)],
            "raticate": [("raticate", True), ("raticate-alola", False)],
        },
    )


def test_two_ways_that_start_from_different_forms_are_two_ways() -> None:
    # A Kantonian Rattata still becomes a Kantonian Raticate and an Alolan one becomes an Alolan
    # Raticate, and a game holding both holds both ways. Reading the newer detail as a
    # replacement is what left the Let's Go pair unable to evolve a Kantonian Graveler.
    forms = [
        form("rattata-alola", "rattata", "lets-go-pikachu"),
        form("raticate-alola", "raticate", "lets-go-pikachu"),
    ]

    methods = evolution_encounters(
        rattata_api(),
        game_id="lets-go-pikachu",
        version_group="lets-go-pikachu-lets-go-eevee",
        species=["rattata", "raticate"],
        forms=forms,
        all_forms=forms,
    )

    assert sorted(one.target.form or "-" for one in methods) == ["-", "raticate-alola"]


def test_a_way_that_starts_from_the_same_form_is_still_replaced() -> None:
    # The other side of it, and the reason this is not simply "keep everything": a Pikachu is
    # one Pokemon, both details ask for that one Pokemon, and what a Thunder Stone makes of it
    # in Alola is an Alolan Raichu and nothing else.
    forms = [form("raichu-alola", "raichu", "sun")]

    methods = evolution_encounters(
        raichu_api(),
        game_id="sun",
        version_group="sun-moon",
        species=["pikachu", "raichu"],
        forms=forms,
        all_forms=forms,
    )

    assert [one.target.form for one in methods] == ["raichu-alola"]


def test_a_form_a_game_says_it_cannot_make_lets_the_older_way_through() -> None:
    # Kanto is not Alola. The Let's Go pair holds the Alolan Raichu - a trader hands one over -
    # so nothing about the form table refuses that rule, and only the game's own word does.
    # What it falls back to is the Raichu a Thunder Stone has made since 1996.
    forms = [form("raichu-alola", "raichu", "lets-go-pikachu")]

    methods = evolution_encounters(
        raichu_api(),
        game_id="lets-go-pikachu",
        version_group="lets-go-pikachu-lets-go-eevee",
        species=["pikachu", "raichu"],
        forms=forms,
        all_forms=forms,
        excluded={"raichu-alola": "a Thunder Stone in Kanto makes the Kantonian one"},
    )

    assert [one.target.form for one in methods] == [None]


def test_the_newest_way_is_the_newest_way_this_game_has() -> None:
    # The Let's Go pair is later than Alola and is Kanto: a Thunder Stone there makes the Raichu
    # it made in 1996. Taking the newest rule and stopping left those two unable to evolve a
    # Pikachu at all, and nine more of Kanto's lines with it - every species Alola drew twice.
    methods = evolution_encounters(
        raichu_api(),
        game_id="lets-go-pikachu",
        version_group="lets-go-pikachu-lets-go-eevee",
        species=["pikachu", "raichu"],
        # Step 8 has not written this pair's forms, and when it does an Alolan Raichu will not
        # be among the ones a Thunder Stone makes here.
        forms=[],
        all_forms=[form("raichu-alola", "raichu", "sun")],
    )

    assert len(methods) == 1
    assert methods[0].target.species == "raichu"
    assert methods[0].target.form is None


def test_a_game_that_does_have_the_newest_ways_form_still_gets_it() -> None:
    # The other side of the same rule: Alola has the Alolan Raichu, so nothing falls back and a
    # Thunder Stone there makes no Kantonian one.
    forms = [form("raichu-alola", "raichu", "sun")]

    methods = evolution_encounters(
        raichu_api(),
        game_id="sun",
        version_group="sun-moon",
        species=["pikachu", "raichu"],
        forms=forms,
        all_forms=forms,
    )

    assert [one.target.form for one in methods] == ["raichu-alola"]


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



# ---------------------------------------------------------------------------
# The ways PokeAPI does not carry, which took twenty-nine games to need.
# ---------------------------------------------------------------------------


def test_the_hand_written_ways_are_all_hisuis_and_all_use_an_item() -> None:
    # Legends: Arceus has no held items and no in-game trade, and between them those two facts
    # break every trade evolution in the series. Twelve pairs, and the source has a detail for
    # none of them.
    assert len(NOT_IN_THE_SOURCE) == 12
    assert {one.version_group for one in NOT_IN_THE_SOURCE} == {"legends-arceus"}
    assert {one.trigger for one in NOT_IN_THE_SOURCE} == {EvolutionTrigger.USE_ITEM}

    # Four needed a cable and nothing else, and one page names all four.
    cord = [one for one in NOT_IN_THE_SOURCE if one.page == "Linking_Cord"]
    assert {one.to_species for one in cord} == {"alakazam", "machamp", "golem", "gengar"}

    # The other eight were traded holding something, and each item's own page says the same
    # sentence in its own words.
    assert {one.page for one in NOT_IN_THE_SOURCE} - {"Linking_Cord"} == {
        "Metal_Coat",
        "Protector",
        "Electirizer",
        "Magmarizer",
        "Up-Grade",
        "Dubious_Disc",
        "Reaper_Cloth",
    }


def test_a_hand_written_way_replaces_the_one_the_source_gave() -> None:
    chains = {
        "1": link(
            "kadabra",
            [],
            [link("alakazam", [detail("trade", "red-blue")])],
        )
    }
    api = FakeApi(chains, species={"kadabra": "1", "alakazam": "1"})

    hisui = evolution_encounters(
        api, game_id="legends-arceus", version_group="legends-arceus",
        species=["kadabra", "alakazam"],
    )

    [one] = hisui
    assert one.rule == "kadabra-to-alakazam-legends-arceus"

    # And it cites the page it was read from rather than a chain the claim is not in.
    assert one.source.source == "bulbapedia"
    assert one.source.url.endswith("Linking_Cord")


def test_an_older_game_keeps_the_way_it_always_had() -> None:
    # The guard that matters: a way added for Hisui must not reach back. Sword is older than
    # Legends: Arceus, so its Kadabra is still traded.
    chains = {
        "1": link(
            "kadabra",
            [],
            [link("alakazam", [detail("trade", "red-blue")])],
        )
    }
    api = FakeApi(chains, species={"kadabra": "1", "alakazam": "1"})

    [one] = evolution_encounters(
        api, game_id="sword", version_group="sword-shield",
        species=["kadabra", "alakazam"],
    )

    assert one.rule == "kadabra-to-alakazam-red-blue"
    assert one.source.source == "pokeapi"


def test_a_hand_written_way_only_joins_the_chain_it_belongs_to() -> None:
    # Asking about a chain that has nothing to do with any of the twelve must not drag them in.
    chains = {"1": link("magikarp", [], [link("gyarados", [detail("level-up", "red-blue")])])}
    api = FakeApi(chains, species={"magikarp": "1", "gyarados": "1"})

    rules = evolution_rules(api, chains=["1"])

    assert [one.id for one in rules] == ["magikarp-to-gyarados"]
