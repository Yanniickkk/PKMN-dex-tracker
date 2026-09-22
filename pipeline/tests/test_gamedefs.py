"""What each game says about itself, and how the registry handles edges between games.

Phase 2 step 1 is exactly this: a game entity and the routes it brings. These pin what is easy
to get subtly wrong later - a dex source, a National Dex cap, an edge pointing at nothing.
"""

from __future__ import annotations

import pytest

from livingdex_pipeline.build import default_registry
from livingdex_pipeline.gamedefs import emerald, hoenn, platinum, ruby, sapphire
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


def pal_park(left: str, right: str) -> TransferEdge:
    return TransferEdge(
        **{"from": left},
        to=right,
        mechanism=TransferMechanism.PAL_PARK,
        direction=TransferDirection.ONE_WAY,
        filter=AllSpeciesFilter(),
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

    # Only ever handed out at a distribution. Saying so is what keeps it out of the list of
    # things the data is missing.
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


def test_emerald_says_which_events_handed_out_what_it_cannot_produce() -> None:
    # Step 7: an event does not make an entry obtainable, but it is the answer to "then where
    # does one come from at all", and every one of the six had one.
    api = FakeApi([(1, "zangoose"), (2, "surskit"), (3, "roselia"), (4, "treecko")])

    entries = {
        entry.target.species: entry for entry in emerald.build(context("emerald", api)).dex_entries
    }

    for species in ("zangoose", "surskit", "roselia"):
        assert "event" in (entries[species].unobtainable_reason or "").lower()

    # The reason it cannot be caught still comes first; the event is the second sentence.
    assert (entries["zangoose"].unobtainable_reason or "").startswith("Ruby only")
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

    assert registry.game_ids == ["emerald", "platinum", "ruby", "sapphire"]
    assert [(edge.from_, edge.to) for edge in registry.edges] == [
        ("emerald", "platinum"),
        ("emerald", "ruby"),
        ("emerald", "sapphire"),
        ("ruby", "sapphire"),
    ]
    # Every Hoenn cartridge names FireRed and LeafGreen, and neither is written yet.
    assert {edge.to for _, edge in registry.held_back_edges} == {"firered", "leafgreen"}


def test_a_both_ways_route_is_one_route_however_many_ends_declare_it() -> None:
    # Ruby names Emerald, Emerald names Ruby. The graph holds the route once.
    trades = [
        (edge.from_, edge.to)
        for edge in default_registry().edges
        if edge.mechanism is TransferMechanism.TRADE
    ]

    assert len(trades) == len(set(frozenset(pair) for pair in trades))


# --- Ruby and Sapphire ------------------------------------------------------------------------


def test_the_pair_are_two_games_that_name_each_other() -> None:
    both = {
        ruby.GAME_ID: ruby.build(context("ruby")).game,
        sapphire.GAME_ID: sapphire.build(context("sapphire")).game,
    }

    # Two entities, not one "Ruby/Sapphire" row: version exclusives are the whole point, and a
    # player links one of them without linking the other.
    assert sorted(both) == ["ruby", "sapphire"]
    assert both["ruby"].pair_partner == "sapphire"
    assert both["sapphire"].pair_partner == "ruby"
    assert both["ruby"].title != both["sapphire"].title


def test_the_pair_share_what_hoenn_gives_them() -> None:
    for game in (ruby.build(context("ruby")).game, sapphire.build(context("sapphire")).game):
        assert game.generation == 3
        assert game.region == "Hoenn"
        assert game.national_dex_through == 386
        assert game.dex_source is DexSource.NATIONAL_DEX


def test_the_pair_were_drawn_from_one_sheet_and_emerald_from_another() -> None:
    # One directory for the two of them, so the build fetches it once however many games name
    # it. Emerald redrew the set later, which is why the third version points somewhere else.
    ruby_set = ruby.build(context("ruby")).game.sprite_set
    sapphire_set = sapphire.build(context("sapphire")).game.sprite_set

    assert ruby_set == sapphire_set == "generation-iii/ruby-sapphire"
    assert ruby_set != emerald.SPRITE_SET


def test_each_of_the_pair_trades_with_every_other_cartridge_but_itself() -> None:
    for module in (ruby, sapphire):
        partners = {edge.to for edge in module.edges()}

        assert module.GAME_ID not in partners
        assert partners == set(hoenn.GBA_CARTRIDGES) - {module.GAME_ID}


def test_the_pair_show_the_same_hoenn_dex_as_emerald() -> None:
    api = FakeApi([(1, "treecko"), (202, "deoxys")])

    for module in (ruby, sapphire):
        data = module.build(context(module.GAME_ID, api))

        # The same entries and the same numbering. Only the game id differs.
        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "treecko"),
            (202, "deoxys"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)

    # Not "updated-hoenn", which is Omega Ruby and Alpha Sapphire's 211.
    assert set(api.asked_for) == {"hoenn"}


def exclusive(pokemon: str, ruby_rate: int, sapphire_rate: int) -> dict:
    """One species on one route, at a different rate in each half of the pair."""
    return {
        pokemon: [
            {
                "location_area": {"name": "hoenn-route-101-area"},
                "version_details": [
                    {
                        "version": {"name": version},
                        "encounter_details": [
                            {
                                "min_level": 3,
                                "max_level": 4,
                                "chance": rate,
                                "method": {"name": "walk"},
                                "condition_values": [],
                            }
                        ],
                    }
                    for version, rate in (("ruby", ruby_rate), ("sapphire", sapphire_rate))
                ],
            }
        ]
    }


def test_each_half_reads_its_own_version_of_the_encounter_table() -> None:
    # The version is the whole difference between the two files, so it had better be the thing
    # that decides what comes out.
    for module, rate in ((ruby, 30), (sapphire, 70)):
        api = FakeApi([(1, "seedot")], exclusive("seedot", ruby_rate=30, sapphire_rate=70))

        methods = module.build(context(module.GAME_ID, api)).acquisition_methods
        wild = [one for one in methods if one.kind == "wild"]

        assert [one.rate_percent for one in wild] == [rate]
        assert all(one.game == module.GAME_ID for one in wild)


def test_a_species_only_the_other_half_has_brings_no_slot() -> None:
    # Zangoose is on Ruby and Seviper on Sapphire. A cartridge that never meets one says so by
    # having nothing to say, not by inventing an empty slot.
    api = FakeApi(
        [(1, "zangoose")],
        {
            "zangoose": [
                {
                    "location_area": {"name": "hoenn-route-101-area"},
                    "version_details": [
                        {
                            "version": {"name": "ruby"},
                            "encounter_details": [
                                {
                                    "min_level": 30,
                                    "max_level": 30,
                                    "chance": 10,
                                    "method": {"name": "walk"},
                                    "condition_values": [],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    )

    def wild_of(module):
        methods = module.build(context(module.GAME_ID, api)).acquisition_methods
        return [one for one in methods if one.kind == "wild"]

    # The trades and the day care are tables rather than fetches, so they turn up either way.
    assert len(wild_of(ruby)) == 1
    assert wild_of(sapphire) == []


def test_the_pair_mark_what_only_the_other_half_keeps() -> None:
    api = FakeApi([(1, "lotad"), (2, "seedot"), (3, "treecko")])

    ruby_entries = {
        entry.target.species: entry for entry in ruby.build(context("ruby", api)).dex_entries
    }
    sapphire_entries = {
        entry.target.species: entry
        for entry in sapphire.build(context("sapphire", api)).dex_entries
    }

    # Each half names the other, and neither marks what it has itself.
    assert ruby_entries["lotad"].unobtainable_reason.startswith(
        "Sapphire only in Generation 3; trade one in"
    )
    assert ruby_entries["seedot"].unobtainable_reason is None
    assert sapphire_entries["seedot"].unobtainable_reason.startswith(
        "Ruby only in Generation 3; trade one in"
    )
    assert sapphire_entries["lotad"].unobtainable_reason is None
    # The starter is in both, so neither says anything about it.
    assert ruby_entries["treecko"].unobtainable_reason is None
    assert sapphire_entries["treecko"].unobtainable_reason is None


def test_the_exclusives_mirror_each_other_exactly() -> None:
    # The same number each and no overlap: that is what a version pair is, and a species in both
    # lists would mean one of the two tables is wrong.
    left = set(ruby.ONLY_ON_SAPPHIRE)
    right = set(sapphire.ONLY_ON_RUBY)

    assert len(left) == len(right)
    assert not left & right
    # Banette and Dusclops were in these lists and should not have been: each cartridge catches
    # the stage below and evolves it. `unobtainable-entries-really-are` is what guards it now.
    assert "banette" not in left
    assert "dusclops" not in right


def test_step_seven_says_which_events_handed_out_what_cannot_be_caught() -> None:
    api = FakeApi([(1, "lotad"), (2, "kyogre"), (3, "deoxys")])

    entries = {
        entry.target.species: entry.unobtainable_reason
        for entry in ruby.build(context("ruby", api)).dex_entries
    }

    # The reason it cannot be caught comes first; the event is the sentence after it.
    assert entries["lotad"].startswith("Sapphire only")
    assert "Fifth Campaign" in entries["lotad"]
    # A legendary that never had a Generation 3 giveaway says nothing extra rather than guessing.
    assert entries["kyogre"] == "Sapphire only in Generation 3; trade one in"
    # Deoxys had two distributions of its own, which is the answer step 5 left open.
    assert "Doel Deoxys" in entries["deoxys"]


def test_the_three_cartridges_word_a_shared_event_once() -> None:
    # Emerald was covered by the same 2006 campaign, so the sentence lives in one place.
    assert hoenn.FIFTH_CAMPAIGN.lower() in hoenn.only_on("Ruby", hoenn.FIFTH_CAMPAIGN).lower()
    assert emerald.UNOBTAINABLE["jirachi"] == hoenn.JIRACHI_REASON


def test_both_halves_say_the_same_thing_about_jirachi() -> None:
    # Nothing in any Generation 3 game produces one, so the three cartridges share one sentence.
    api = FakeApi([(201, "jirachi")])

    reasons = {
        module.build(context(module.GAME_ID, api)).dex_entries[0].unobtainable_reason
        for module in (ruby, sapphire)
    }

    assert len(reasons) == 1
    assert "Bonus Disc" in reasons.pop()


def test_the_pair_share_their_three_in_game_trades() -> None:
    for module in (ruby, sapphire):
        methods = module.build(context(module.GAME_ID)).acquisition_methods
        trades = [one for one in methods if one.kind == "trade"]

        assert [(one.target.species, one.wants.species) for one in trades] == [
            ("makuhita", "slakoth"),
            ("skitty", "pikachu"),
            ("corsola", "bellossom"),
        ]
        assert all(one.game == module.GAME_ID for one in trades)
        assert all(one.source.source == "bulbapedia" for one in trades)


def test_the_pair_hatch_the_same_three_babies() -> None:
    for module in (ruby, sapphire):
        methods = module.build(context(module.GAME_ID)).acquisition_methods
        eggs = {one.target.species: one for one in methods if one.kind == "breeding"}

        assert sorted(eggs) == ["azurill", "igglybuff", "pichu"]
        assert eggs["pichu"].location == "Route 117, Pokemon Day Care"
        # Wynaut is not here: both cartridges hand one over in an egg already.
        assert "wynaut" not in eggs


def test_the_pair_evolve_by_their_own_version_group() -> None:
    api = FakeApi([(1, "treecko"), (2, "grovyle")])

    for module in (ruby, sapphire):
        methods = module.build(context(module.GAME_ID, api)).acquisition_methods
        evolutions = [one for one in methods if one.kind == "evolution"]

        assert [one.target.species for one in evolutions] == ["grovyle"]

    # Emerald is its own version group; the pair are one. Both are Generation 3 and the
    # difference is the point: an ordering, not a generation.
    assert hoenn.PAIR_VERSION_GROUP == "ruby-sapphire"
    assert emerald.POKEAPI_VERSION_GROUP == "emerald"


def test_the_pair_share_one_gift_table() -> None:
    # They agree about every species they both have, so the table is written once. A key the
    # other half never sees simply never matches.
    assert ruby.hoenn.PAIR_GIFTS is sapphire.hoenn.PAIR_GIFTS
    assert "groudon" not in ruby.hoenn.PAIR_GIFTS
    assert ruby.hoenn.PAIR_GIFTS["treecko"].npc == "Professor Birch"


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


def test_one_both_ways_route_written_from_either_end_is_still_one_route() -> None:
    # Which end wrote it down is not part of what the route is, and the app expands a both-ways
    # edge into both directions itself - so keeping the mirror image would show it twice.
    registry = GameRegistry()
    registry.register(
        "emerald",
        lambda _: stub("emerald"),
        [trade("emerald", "ruby"), trade("ruby", "emerald")],
    )
    registry.register("ruby", lambda _: stub("ruby"))

    assert len(registry.edges) == 1


def test_two_one_way_routes_between_the_same_games_stay_two() -> None:
    # Pal Park carries a Generation 3 cartridge into Platinum and never the other way, so the
    # same two games in the other order is a different claim rather than the same one repeated.
    registry = GameRegistry()
    registry.register(
        "emerald",
        lambda _: stub("emerald"),
        [pal_park("emerald", "platinum"), pal_park("platinum", "emerald")],
    )
    registry.register("platinum", lambda _: stub("platinum"))

    assert len(registry.edges) == 2


def test_a_held_back_edge_names_the_game_that_declared_it() -> None:
    # A misspelt id looks like a game that has not been written yet; the name is what tells them
    # apart, so it is reported rather than dropped in silence.
    registry = GameRegistry()
    registry.register("emerald", lambda _: stub("emerald"), [trade("emerald", "rubby")])

    assert [(who, edge.to) for who, edge in registry.held_back_edges] == [("emerald", "rubby")]
