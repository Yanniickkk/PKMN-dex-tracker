"""What each game says about itself, and how the registry handles edges between games.

Phase 2 step 1 is exactly this: a game entity and the routes it brings. These pin what is easy
to get subtly wrong later - a dex source, a National Dex cap, an edge pointing at nothing.
"""

from __future__ import annotations

import pytest

from livingdex_pipeline.build import default_registry
from livingdex_pipeline.gamedefs import emerald, platinum
from livingdex_pipeline.games import BuildContext, GameRegistry
from livingdex_pipeline.models import (
    AllSpeciesFilter,
    DexSource,
    Game,
    GameData,
    GameRelease,
    GiftKind,
    TransferDirection,
    TransferEdge,
    TransferMechanism,
)

#: One chain, enough for the two species the fake dex holds. Grovyle's entry is stamped with
#: the version group Ruby and Sapphire introduced it in, the same way PokeAPI stamps a real one.
TREECKO_CHAIN = {
    "species": {"name": "treecko"},
    "evolves_to": [
        {
            "species": {"name": "grovyle"},
            "evolution_details": [
                {
                    "trigger": {"name": "level-up"},
                    "version_group": {"name": "ruby-sapphire"},
                    "min_level": 16,
                }
            ],
            "evolves_to": [],
        }
    ],
}

#: Where the version groups the tests use sit in the series, as PokeAPI orders them.
VERSION_GROUP_ORDER = {"ruby-sapphire": 5, "emerald": 6, "diamond-pearl": 8}


class FakeApi:
    """Stands in for PokeAPI. Records what was asked for, answers with a short dex."""

    def __init__(
        self,
        entries: list[tuple[int, str]] | None = None,
        encounters: dict[str, list] | None = None,
    ) -> None:
        self.asked_for: list[str] = []
        self._entries = entries if entries is not None else [(1, "treecko"), (2, "grovyle")]
        self._encounters = encounters or {}

    def pokedex(self, name: str, *, refresh: bool = False) -> list[tuple[int, str]]:
        self.asked_for.append(name)
        return list(self._entries)

    def default_pokemon(self, species: str, *, refresh: bool = False) -> str:
        return species

    def encounters(self, pokemon: str, *, refresh: bool = False) -> list:
        return self._encounters.get(pokemon, [])

    def evolution_chain(self, species: str, *, refresh: bool = False) -> str:
        return "treecko"

    def resource(self, path: str, *, refresh: bool = False) -> dict:
        if path.startswith("location-area/"):
            return {"location": {"name": "hoenn-route-101"}}

        if path.startswith("evolution-chain/"):
            return {"chain": TREECKO_CHAIN}

        if path.startswith("version-group/"):
            return {"order": VERSION_GROUP_ORDER[path.removeprefix("version-group/")]}

        return {"names": [{"language": {"name": "en"}, "name": "Route 101"}]}


def context(game_id: str, api: FakeApi | None = None) -> BuildContext:
    return BuildContext(game_id=game_id, refresh=False, api=api or FakeApi())


def stub(game_id: str) -> GameData:
    return GameData(
        game=Game(
            id=game_id,
            title=game_id.title(),
            version=game_id.title(),
            generation=3,
            region="Hoenn",
            release=GameRelease.CARTRIDGE,
            national_dex_through=386,
            dex_source=DexSource.NATIONAL_DEX,
        )
    )


def trade(left: str, right: str) -> TransferEdge:
    return TransferEdge(
        **{"from": left},
        to=right,
        mechanism=TransferMechanism.TRADE,
        direction=TransferDirection.BOTH_WAYS,
        filter=AllSpeciesFilter(),
    )


# --- Emerald ----------------------------------------------------------------------------------


def test_emerald_builds_from_the_national_dex_through_386() -> None:
    game = emerald.build(context("emerald")).game

    assert game.id == "emerald"
    assert game.title == "Pokémon Emerald Version"
    assert game.generation == 3
    assert game.region == "Hoenn"
    assert game.release is GameRelease.CARTRIDGE
    assert game.dex_source is DexSource.NATIONAL_DEX
    assert game.national_dex_through == 386
    # The third version of Ruby and Sapphire, not half of a pair.
    assert game.pair_partner is None


def test_emerald_lists_the_generation_3_hoenn_dex_with_its_own_numbers() -> None:
    api = FakeApi([(1, "treecko"), (202, "deoxys")])

    data = emerald.build(context("emerald", api))

    # Not "updated-hoenn", which is the 211-entry dex of Omega Ruby and Alpha Sapphire.
    assert api.asked_for == ["hoenn"]
    assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
        (1, "treecko"),
        (202, "deoxys"),
    ]
    assert all(entry.game == "emerald" for entry in data.dex_entries)
    # The dex list is the game's own; what a living dex here aims at is the National Dex, which
    # the entity carries.
    assert all(entry.unobtainable_reason is None for entry in data.dex_entries)


def test_emerald_marks_what_no_amount_of_playing_it_will_produce() -> None:
    api = FakeApi([(200, "jirachi"), (202, "deoxys")])

    entries = {
        entry.target.species: entry for entry in emerald.build(context("emerald", api)).dex_entries
    }

    # Only ever handed out with the Colosseum Bonus Disc. Saying so is what keeps it out of the
    # list of things the data is missing.
    assert "Bonus Disc" in (entries["jirachi"].unobtainable_reason or "")
    assert entries["deoxys"].unobtainable_reason is None


def test_emerald_marks_the_hoenn_dex_entries_its_own_grass_never_holds() -> None:
    api = FakeApi([(1, "roselia"), (2, "meditite"), (3, "surskit"), (4, "treecko")])

    entries = {
        entry.target.species: entry for entry in emerald.build(context("emerald", api)).dex_entries
    }

    # In Ruby and Sapphire's grass and not in Emerald's, which is the game rather than a hole in
    # the data. The transfer graph is how the entry gets filled.
    assert "Ruby and Sapphire only" in (entries["roselia"].unobtainable_reason or "")
    assert "Ruby and Sapphire only" in (entries["meditite"].unobtainable_reason or "")
    # Nearly obtainable, which is worth saying in full: the swarm is real, and it needs a second
    # cartridge to turn up.
    assert "mixing records" in (entries["surskit"].unobtainable_reason or "")
    assert entries["treecko"].unobtainable_reason is None


def test_emerald_records_its_four_in_game_trades() -> None:
    methods = emerald.build(context("emerald")).acquisition_methods
    trades = [method for method in methods if method.kind == "trade"]

    assert [(trade.target.species, trade.wants.species) for trade in trades] == [
        ("seedot", "ralts"),
        ("plusle", "volbeat"),
        ("horsea", "bagon"),
        ("meowth", "skitty"),
    ]
    assert trades[0].location == "Rustboro City"
    # The Battle Frontier is post-game, and the only one of the four that has to say so.
    assert "Battle Frontier" in (trades[3].requirement or "")
    assert all(trade.source.source == "bulbapedia" for trade in trades)


def test_emerald_hatches_the_babies_nothing_else_in_it_produces() -> None:
    methods = emerald.build(context("emerald")).acquisition_methods
    eggs = {method.target.species: method for method in methods if method.kind == "breeding"}

    assert sorted(eggs) == ["azurill", "igglybuff", "pichu"]
    assert [parent.species for parent in eggs["azurill"].parents] == ["marill", "azumarill"]
    assert eggs["pichu"].location == "Route 117, Pokemon Day Care"
    # Generation 3 asks for no incense; that is a Generation 4 rule.
    assert all(egg.requirement is None for egg in eggs.values())


def test_emerald_evolves_what_its_own_generation_can() -> None:
    api = FakeApi([(1, "treecko"), (2, "grovyle")])

    methods = emerald.build(context("emerald", api)).acquisition_methods
    evolutions = [method for method in methods if method.kind == "evolution"]

    assert [one.target.species for one in evolutions] == ["grovyle"]
    assert evolutions[0].rule == "treecko-to-grovyle"


def test_emerald_names_who_hands_over_a_starter() -> None:
    api = FakeApi(
        [(1, "treecko")],
        {
            "treecko": [
                {
                    "location_area": {"name": "hoenn-route-101-area"},
                    "version_details": [
                        {
                            "version": {"name": "emerald"},
                            "encounter_details": [
                                {
                                    "min_level": 5,
                                    "max_level": 5,
                                    "chance": 100,
                                    "method": {"name": "gift"},
                                    "condition_values": [],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    )

    methods = emerald.build(context("emerald", api)).acquisition_methods

    # The trades and the day care are tables rather than fetches, so they turn up whatever the
    # encounter data says. The gift is the one this test is about.
    gift = next(method for method in methods if method.kind == "gift")
    # PokeAPI says "gift"; that it is one of three starters from Birch is Emerald's own business.
    assert gift.gift_kind is GiftKind.STARTER
    assert gift.npc == "Professor Birch"
    assert gift.location == "Route 101"
    assert gift.level == 5


def test_a_builder_without_the_api_client_says_so_rather_than_failing_deep_inside() -> None:
    with pytest.raises(RuntimeError, match="needs the PokeAPI client"):
        emerald.build(BuildContext(game_id="emerald", refresh=False))


def test_emerald_trades_both_ways_with_every_other_generation_3_cartridge() -> None:
    edges = emerald.edges()

    assert {edge.to for edge in edges} == {"ruby", "sapphire", "firered", "leafgreen"}
    assert all(edge.from_ == "emerald" for edge in edges)
    assert all(edge.direction is TransferDirection.BOTH_WAYS for edge in edges)
    assert all(edge.mechanism is TransferMechanism.TRADE for edge in edges)
    # Trading inside a generation carries anything the game can hold.
    assert all(isinstance(edge.filter, AllSpeciesFilter) for edge in edges)


def test_emerald_does_not_claim_pal_park_itself() -> None:
    # It is one way and its National Dex limit is a fact about the game that receives.
    assert all(edge.mechanism is not TransferMechanism.PAL_PARK for edge in emerald.edges())

    receiving = [edge for edge in platinum.edges() if edge.mechanism is TransferMechanism.PAL_PARK]
    assert [(edge.from_, edge.to) for edge in receiving] == [("emerald", "platinum")]


def test_the_real_registry_emits_only_the_routes_both_of_whose_ends_exist() -> None:
    registry = default_registry()

    assert registry.game_ids == ["emerald", "platinum"]
    assert [(edge.from_, edge.to) for edge in registry.edges] == [("emerald", "platinum")]
    # Emerald's four partners are declared and waiting.
    assert {edge.to for _, edge in registry.held_back_edges} == {
        "ruby",
        "sapphire",
        "firered",
        "leafgreen",
    }


# --- the registry itself ----------------------------------------------------------------------


def test_an_edge_appears_as_soon_as_its_other_end_is_registered() -> None:
    registry = GameRegistry()
    registry.register("emerald", lambda _: stub("emerald"), [trade("emerald", "ruby")])

    assert registry.edges == []

    registry.register("ruby", lambda _: stub("ruby"))

    assert [(edge.from_, edge.to) for edge in registry.edges] == [("emerald", "ruby")]
    assert registry.held_back_edges == []


def test_the_same_edge_declared_from_both_sides_is_written_once() -> None:
    # Neither game should have to know whether the other got there first.
    registry = GameRegistry()
    registry.register("emerald", lambda _: stub("emerald"), [trade("emerald", "ruby")])
    registry.register("ruby", lambda _: stub("ruby"), [trade("emerald", "ruby")])

    assert len(registry.edges) == 1


def test_two_directions_of_one_pair_are_two_edges() -> None:
    # Same pair, opposite ways round: that is two routes, not one written twice.
    registry = GameRegistry()
    registry.register(
        "emerald",
        lambda _: stub("emerald"),
        [trade("emerald", "ruby"), trade("ruby", "emerald")],
    )
    registry.register("ruby", lambda _: stub("ruby"))

    assert len(registry.edges) == 2


def test_a_held_back_edge_names_the_game_that_declared_it() -> None:
    # A misspelt id looks like a game that has not been written yet; the name is what tells them
    # apart, so it is reported rather than dropped in silence.
    registry = GameRegistry()
    registry.register("emerald", lambda _: stub("emerald"), [trade("emerald", "rubby")])

    assert [(who, edge.to) for who, edge in registry.held_back_edges] == [("emerald", "rubby")]
