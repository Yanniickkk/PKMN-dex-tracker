"""Evolution rules, and the version-group arithmetic that decides which ones a game gets."""

from __future__ import annotations

from datetime import date

from livingdex_pipeline.evolutions import evolution_encounters, evolution_rules
from livingdex_pipeline.models import EvolutionTrigger

RETRIEVED_ON = date(2026, 9, 21)

#: Where the version groups these tests use sit in the series, as PokeAPI orders them.
ORDER = {
    "red-blue": 1,
    "gold-silver": 3,
    "ruby-sapphire": 5,
    "emerald": 6,
    "diamond-pearl": 8,
    "black-white": 11,
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

    def __init__(self, chains: dict[str, dict], species: dict[str, str] | None = None) -> None:
        self._chains = chains
        self._species = species or {}

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
        retrieved_on=RETRIEVED_ON,
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
        retrieved_on=RETRIEVED_ON,
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
            retrieved_on=RETRIEVED_ON,
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
            retrieved_on=RETRIEVED_ON,
        )
        == []
    )
