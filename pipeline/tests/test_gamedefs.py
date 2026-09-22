"""What each game says about itself, and how the registry handles edges between games.

Phase 2 step 1 is exactly this: a game entity and the routes it brings. These pin what is easy
to get subtly wrong later - a dex source, a National Dex cap, an edge pointing at nothing.
"""

from __future__ import annotations

import pytest

from livingdex_pipeline.build import default_registry
from livingdex_pipeline.gamedefs import (
    diamond,
    ds,
    emerald,
    firered,
    gba,
    hoenn,
    kanto,
    leafgreen,
    pearl,
    platinum,
    ruby,
    sapphire,
    sinnoh,
)
from livingdex_pipeline.games import BuildContext, GameRegistry
from livingdex_pipeline.models import (
    AllSpeciesFilter,
    DexSource,
    Game,
    GameData,
    GameRelease,
    GiftKind,
    PokemonType,
    Species,
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
VERSION_GROUP_ORDER = {
    "ruby-sapphire": 5,
    "emerald": 6,
    "firered-leafgreen": 7,
    "diamond-pearl": 8,
    "platinum": 9,
}


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

    def entries(self) -> list[tuple[int, str]]:
        """The fake dex, without recording that anybody asked for it."""
        return list(self._entries)

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


def context(
    game_id: str, api: FakeApi | None = None, reaches: list[str] | None = None
) -> BuildContext:
    """A builder's context, with a species table that covers the fake dex.

    The species table is what tells a game which species its living dex asks for, and that is
    a longer list than its own Pokedex. These tests mostly care about the Pokedex, so the
    table is built from it - and ``reaches`` adds the ones a test wants the living dex to
    reach past it, which is the whole point of the distinction.
    """
    api = api or FakeApi()
    listed = [name for _, name in api.entries()] + (reaches or [])

    return BuildContext(
        game_id=game_id,
        refresh=False,
        api=api,
        species=[
            Species(
                id=name,
                national_dex_number=number,
                name=name.title(),
                types=[PokemonType.NORMAL],
                evolution_chain=name,
            )
            for number, name in enumerate(dict.fromkeys(listed), start=1)
        ],
    )


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


def test_no_cartridge_claims_pal_park_itself() -> None:
    # It is one way and its National Dex limit is a fact about the game that receives.
    for module in (ruby, sapphire, emerald, firered, leafgreen):
        assert all(edge.mechanism is not TransferMechanism.PAL_PARK for edge in module.edges())


def test_pal_park_takes_a_game_pak_and_does_not_care_which_one() -> None:
    # The machine asks for a Generation 3 cartridge in the slot, so all five routes exist or
    # none do. Platinum listed Emerald alone until FireRed and LeafGreen were written, which
    # sent Ruby and Sapphire into Generation 4 the long way round, by trading into Emerald.
    receiving = [edge for edge in platinum.edges() if edge.mechanism is TransferMechanism.PAL_PARK]

    assert {edge.from_ for edge in receiving} == set(gba.CARTRIDGES)
    assert all(edge.to == "platinum" for edge in receiving)
    assert all(edge.direction is TransferDirection.ONE_WAY for edge in receiving)
    # Nothing above 386 existed to migrate.
    assert all(edge.filter.to == 386 for edge in receiving)


def test_the_sinnoh_pair_are_two_games_that_name_each_other() -> None:
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID)).game for module in (diamond, pearl)
    }

    assert sorted(both) == ["diamond", "pearl"]
    assert both["diamond"].pair_partner == "pearl"
    assert both["pearl"].pair_partner == "diamond"
    assert both["diamond"].title != both["pearl"].title


def test_the_sinnoh_games_are_generation_4_cartridges_reaching_arceus() -> None:
    for module in (diamond, pearl, platinum):
        game = module.build(context(module.GAME_ID)).game

        assert game.generation == 4
        assert game.region == "Sinnoh"
        assert game.national_dex_through == 493
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.released is not None

    # The third version names nobody, which is what separates it from the pair.
    assert platinum.build(context("platinum")).game.pair_partner is None


def test_both_sinnoh_halves_show_the_same_original_sinnoh_dex() -> None:
    api = FakeApi([(1, "turtwig"), (151, "manaphy")])

    for module in (diamond, pearl):
        data = module.build(context(module.GAME_ID, api))

        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "turtwig"),
            (151, "manaphy"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)

    # Not "extended-sinnoh", which is Platinum's 210. Unlike the Hoenn three, the Sinnoh three
    # do not share one regional dex, so the pair's name says whose it is.
    assert set(api.asked_for) == {"original-sinnoh"}


def sinnoh_slot(version: str, chance: int, conditions: list[str]) -> dict:
    return {
        "location_area": {"name": "sinnoh-route-206-area"},
        "version_details": [
            {
                "version": {"name": version},
                "encounter_details": [
                    {
                        "min_level": 15,
                        "max_level": 15,
                        "chance": chance,
                        "method": {"name": "walk"},
                        "condition_values": [{"name": one} for one in conditions],
                    }
                ],
            }
        ],
    }


def test_each_sinnoh_half_reads_its_own_version_of_the_encounter_table() -> None:
    # The version is the whole difference between the two files, so it had better be the thing
    # that decides what comes out.
    for module, rate in ((diamond, 20), (pearl, 45)):
        api = FakeApi(
            [(1, "stunky")],
            {
                "stunky": [
                    sinnoh_slot("diamond", 20, ["swarm-no"]),
                    sinnoh_slot("pearl", 45, ["swarm-no"]),
                ]
            },
        )

        wild = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "wild"
        ]

        assert [one.rate_percent for one in wild] == [rate]
        assert all(one.game == module.GAME_ID for one in wild)


def test_a_sinnoh_slot_that_needs_a_cartridge_underneath_says_so() -> None:
    # Dual-slot mode is the first condition in this dataset that asks for hardware a player may
    # not own. Gengar is in Sinnoh's grass only while a Generation 3 cartridge is in the slot,
    # and a record that left that out would send someone looking for it with nothing in there.
    api = FakeApi([(1, "gengar")], {"gengar": [sinnoh_slot("diamond", 4, ["slot2-ruby"])]})

    wild = [
        one
        for one in diamond.build(context("diamond", api)).acquisition_methods
        if one.kind == "wild"
    ]

    assert len(wild) == 1
    assert "Game Boy Advance slot" in wild[0].requirement


def sinnoh_gift(version: str, method: str, level: int, conditions: list[str]) -> dict:
    return {
        "location_area": {"name": "oreburgh-city-oreburgh-mining-museum"},
        "version_details": [
            {
                "version": {"name": version},
                "encounter_details": [
                    {
                        "min_level": level,
                        "max_level": level,
                        "chance": 100,
                        "method": {"name": method},
                        "condition_values": [{"name": one} for one in conditions],
                    }
                ],
            }
        ],
    }


def test_the_sinnoh_pair_hand_over_the_same_starters() -> None:
    api = FakeApi(
        [(1, "turtwig")],
        {
            "turtwig": [
                sinnoh_gift("diamond", "gift", 5, []),
                sinnoh_gift("pearl", "gift", 5, []),
            ]
        },
    )

    for module in (diamond, pearl):
        gifts = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "gift"
        ]

        assert len(gifts) == 1
        assert gifts[0].gift_kind is GiftKind.STARTER
        assert gifts[0].npc == "Professor Rowan"


def test_each_half_revives_its_own_fossil_and_not_the_other_halfs() -> None:
    # PokeAPI files both fossils under both halves. Bulbapedia is clear that only Diamond's
    # Underground holds a Skull Fossil and only Pearl's an Armor Fossil, so one of the two rows
    # each half is handed is not that half's.
    encounters = {
        "cranidos": [
            sinnoh_gift("diamond", "gift", 20, ["item-skull-fossil"]),
            sinnoh_gift("pearl", "gift", 20, ["item-skull-fossil"]),
        ],
        "shieldon": [
            sinnoh_gift("diamond", "gift", 20, ["item-armor-fossil"]),
            sinnoh_gift("pearl", "gift", 20, ["item-armor-fossil"]),
        ],
    }

    revived = {}
    for module in (diamond, pearl):
        api = FakeApi([(36, "cranidos"), (38, "shieldon")], encounters)
        revived[module.GAME_ID] = {
            one.target.species
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "gift"
        }

    assert revived == {"diamond": {"cranidos"}, "pearl": {"shieldon"}}


def test_all_three_sinnoh_games_offer_the_same_four_trades() -> None:
    # The one table Platinum did not change. It moved the starters, swapped where Porygon comes
    # from and changed the terms on both cover legendaries, and then left these four standing in
    # the same four houses - so the table is not named for the pair.
    offered = {
        module.GAME_ID: [
            (one.target.species, one.wants.species, one.npc)
            for one in module.build(context(module.GAME_ID)).acquisition_methods
            if one.kind == "trade"
        ]
        for module in (diamond, pearl, platinum)
    }

    assert offered["diamond"] == offered["pearl"] == offered["platinum"]
    assert len(offered["platinum"]) == 4


def test_platinum_hatches_the_two_babies_its_longer_dex_asks_for() -> None:
    # The pair hatches nothing: every baby in their 151 is somewhere in Sinnoh's grass. Platinum
    # counts 59 more entries as Sinnoh's, and two of them are babies whose grown forms it has
    # and whose own forms live nowhere in the region.
    eggs = [
        one
        for one in platinum.build(context("platinum")).acquisition_methods
        if one.kind == "breeding"
    ]

    assert [one.target.species for one in eggs] == ["elekid", "magby"]
    assert all(one.location == sinnoh.DAY_CARE for one in eggs)
    # Either stage does. Naming only the unevolved one would make Electivire look like a dead
    # end to anyone who had already evolved theirs.
    assert [parent.species for parent in eggs[0].parents] == ["electabuzz", "electivire"]

    for module in (diamond, pearl):
        methods = module.build(context(module.GAME_ID)).acquisition_methods
        assert [one for one in methods if one.kind == "breeding"] == []


def test_platinum_keeps_all_four_of_the_pairs_exclusives_out() -> None:
    # Emerald took most of Ruby and Sapphire's exclusives in, so a third version being the
    # generous one is the expectation this breaks. Two are Diamond's and two are Pearl's, and
    # the reason has to name the half that actually has them.
    api = FakeApi([(72, "misdreavus"), (74, "murkrow"), (76, "glameow"), (84, "stunky")])

    reasons = {
        entry.target.species: entry.unobtainable_reason
        for entry in platinum.build(context("platinum", api)).dex_entries
    }

    assert reasons["murkrow"].startswith("Diamond only")
    assert reasons["stunky"].startswith("Diamond only")
    assert reasons["misdreavus"].startswith("Pearl only")
    assert reasons["glameow"].startswith("Pearl only")

    # Their evolutions are reachable once one comes over the link, so they are not on the list.
    assert set(platinum.UNOBTAINABLE) == {
        "manaphy",
        "murkrow",
        "stunky",
        "misdreavus",
        "glameow",
    }


def test_the_sinnoh_pair_share_their_four_in_game_trades() -> None:
    both = {
        module.GAME_ID: [
            one
            for one in module.build(context(module.GAME_ID)).acquisition_methods
            if one.kind == "trade"
        ]
        for module in (diamond, pearl)
    }

    # Unlike the gifts, the halves do not disagree here: the same four traders stand in the
    # same four places on both cartridges.
    assert [(one.target.species, one.wants.species) for one in both["diamond"]] == [
        (one.target.species, one.wants.species) for one in both["pearl"]
    ]
    assert {one.npc for one in both["diamond"]} == {"Hilary", "Norton", "Mindy", "Meister"}
    assert all(one.game == module for module, trades in both.items() for one in trades)


def test_the_sinnoh_pair_evolve_by_their_own_version_group() -> None:
    api = FakeApi([(1, "treecko"), (2, "grovyle")])

    for module in (diamond, pearl):
        methods = module.build(context(module.GAME_ID, api)).acquisition_methods
        evolutions = [one for one in methods if one.kind == "evolution"]

        assert [one.target.species for one in evolutions] == ["grovyle"]

    # Sinnoh's own evolutions - the Shiny Stone, the magnetic field, Gallade - are stamped with
    # the pair's group, and asking for any other would lose all of them. The two halves are one
    # group; Platinum is its own, the way Emerald is.
    assert sinnoh.PAIR_VERSION_GROUP == "diamond-pearl"


def test_the_sinnoh_pair_hatch_nothing_the_day_care_alone_produces() -> None:
    # Ruby and Sapphire hatch three because their dex has three babies with no other source.
    # Generation 4 brought most of the baby Pokemon there are and then put them in Sinnoh's own
    # grass, so this pair has none - an absence worth a test, because "we forgot" and "there is
    # nothing to forget" look the same in a file.
    for module in (diamond, pearl):
        methods = module.build(context(module.GAME_ID)).acquisition_methods

        assert [one for one in methods if one.kind == "breeding"] == []


def test_the_sinnoh_pair_mark_what_only_the_other_half_keeps() -> None:
    api = FakeApi([(36, "cranidos"), (38, "shieldon"), (151, "manaphy"), (1, "turtwig")])

    reasons = {
        module.GAME_ID: {
            entry.target.species: entry.unobtainable_reason
            for entry in module.build(context(module.GAME_ID, api)).dex_entries
        }
        for module in (diamond, pearl)
    }

    # The generation is the one this pair is in. It used to be spelled out per module, which is
    # how a Generation 4 game would have told a player to trade one in from Generation 3.
    assert reasons["diamond"]["shieldon"].startswith("Pearl only in Generation 4")
    assert reasons["pearl"]["cranidos"].startswith("Diamond only in Generation 4")

    # A fossil travels held by a traded Pokemon, so the link offers two ways rather than one.
    assert "holding the Armor Fossil" in reasons["diamond"]["shieldon"]
    assert "holding the Skull Fossil" in reasons["pearl"]["cranidos"]

    # Nothing in Sinnoh produces a Manaphy, on either half.
    assert reasons["diamond"]["manaphy"] == reasons["pearl"]["manaphy"]
    assert "Pokemon Ranger" in reasons["diamond"]["manaphy"]

    # And what the pair does produce says nothing at all.
    assert reasons["diamond"]["turtwig"] is None


def test_step_seven_found_nothing_for_the_sinnoh_exclusives() -> None:
    # The opposite of the Kanto pair, where one day in a shop in 2004 covered most of the
    # fourteen. Not one distribution was ever for Diamond or Pearl, and a test says so because
    # "we looked and there is nothing" and "nobody has looked yet" are the same empty dict.
    for module in (diamond, pearl):
        exclusives = [
            value
            for name, value in vars(module).items()
            if name.startswith("ONLY_ON_") or name.endswith("_EVENT")
        ]
        events = [
            event
            for value in exclusives
            for event in (value.values() if isinstance(value, dict) else [value])
        ]

        assert events
        assert all(event is None for event in events)


def test_both_sinnoh_halves_say_the_same_thing_about_manaphy() -> None:
    # Neither cartridge produces one, and the nine distributions that did were for both.
    assert diamond.UNOBTAINABLE["manaphy"] == pearl.UNOBTAINABLE["manaphy"]
    assert "Pokemon Ranger" in diamond.UNOBTAINABLE["manaphy"]
    # The event is the second sentence of the reason, so it is joined with its first letter
    # lifted: "... to this one. Nine distributions ...".
    assert sinnoh.PAIR_MANAPHY_EVENT.lower() in diamond.UNOBTAINABLE["manaphy"].lower()


def test_platinum_was_not_at_seven_of_the_nine_manaphy_giveaways() -> None:
    # Seven of them had come and gone before Platinum was released, so sharing the pair's
    # sentence told a Platinum player to have been at a Toys "R" Us in 2007 for a game that did
    # not exist until 2008. Only the last two list it among their games.
    pair = diamond.UNOBTAINABLE["manaphy"]
    third = platinum.UNOBTAINABLE["manaphy"]

    assert pair != third
    assert "Pokemon Ranger" in third
    assert "Toys" in pair
    assert "Toys" not in third
    assert "Summer Nintendo Zone" in third


def test_the_sinnoh_pair_were_drawn_from_one_sheet_of_their_own() -> None:
    # One directory for the two of them, so the build fetches it once however many games name
    # it. Platinum redrew them - not one of its 493 files matches the pair's byte for byte - so
    # its sheet is its own and the pair's is named for the pair: a Sinnoh player sees different
    # sprites depending on which of the three is in the slot.
    sets = {module.build(context(module.GAME_ID)).game.sprite_set for module in (diamond, pearl)}
    third = platinum.build(context("platinum")).game.sprite_set

    assert sets == {"generation-iv/diamond-pearl"}
    assert third == "generation-iv/platinum"
    assert third not in sets


def test_the_sinnoh_exclusives_mirror_each_other_exactly() -> None:
    # A pair that keeps four from one half and five from the other is a pair with a mistake in
    # it. Manaphy is on both lists and belongs to neither half.
    assert len(diamond.UNOBTAINABLE) == len(pearl.UNOBTAINABLE)
    assert set(diamond.UNOBTAINABLE) & set(pearl.UNOBTAINABLE) == {"manaphy"}


def test_platinum_shows_the_extended_sinnoh_dex_and_the_pair_does_not() -> None:
    api = FakeApi([(1, "turtwig"), (152, "rotom"), (210, "giratina")])

    data = platinum.build(context("platinum", api))

    assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
        (1, "turtwig"),
        (152, "rotom"),
        (210, "giratina"),
    ]
    assert all(entry.game == "platinum" for entry in data.dex_entries)

    # The whole point of the two names. Emerald shows the Hoenn pair's dex; Platinum does not
    # show Diamond and Pearl's, and a third version that borrowed the pair's would be 59 short.
    assert set(api.asked_for) == {"extended-sinnoh"}
    assert sinnoh.EXTENDED_DEX != sinnoh.PAIR_DEX


def test_platinum_reads_its_own_version_of_the_encounter_table() -> None:
    api = FakeApi(
        [(1, "stunky")],
        {
            "stunky": [
                sinnoh_slot("diamond", 20, ["swarm-no"]),
                sinnoh_slot("platinum", 35, ["swarm-no"]),
            ]
        },
    )

    wild = [
        one
        for one in platinum.build(context("platinum", api)).acquisition_methods
        if one.kind == "wild"
    ]

    assert [one.rate_percent for one in wild] == [35]
    assert all(one.game == "platinum" for one in wild)


def test_a_step_that_has_not_been_gathered_yet_brings_nothing_rather_than_bare_rows() -> None:
    # A game arrives with its encounters and picks its tables up as the steps run. PokeAPI would
    # hand over its gift rows the whole time, with "gift" for a starter and nobody's name on
    # them, and taking those would be step 4 done badly rather than step 4 not done.
    api = FakeApi(
        [(1, "turtwig")],
        {
            "turtwig": [
                {
                    "location_area": {"name": "sinnoh-route-201-area"},
                    "version_details": [
                        {
                            "version": {"name": "platinum"},
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
    entries = platinum.dex_entries(context("platinum", api))

    without = sinnoh.acquisition_methods(
        context("platinum", api),
        game_id="platinum",
        version="platinum",
        entries=entries,
    )
    with_table = sinnoh.acquisition_methods(
        context("platinum", api),
        game_id="platinum",
        version="platinum",
        entries=entries,
        gifts=platinum.GIFTS,
    )

    assert [one for one in without if one.kind == "gift"] == []
    assert [one.target.species for one in with_table if one.kind == "gift"] == ["turtwig"]


def test_a_generation_4_cartridge_brings_its_trades_and_its_pal_park_together() -> None:
    # The two kinds of route come from one call, because Platinum once declared them in two
    # places and only one of them grew when Ruby and Sapphire arrived.
    for module in (diamond, pearl, platinum):
        edges = module.edges()

        trades = {edge.to for edge in edges if edge.mechanism is TransferMechanism.TRADE}
        migrations = [edge for edge in edges if edge.mechanism is TransferMechanism.PAL_PARK]

        assert trades == set(ds.CARTRIDGES) - {module.GAME_ID}
        assert {edge.from_ for edge in migrations} == set(gba.CARTRIDGES)
        assert all(edge.to == module.GAME_ID for edge in migrations)
        assert all(edge.direction is TransferDirection.ONE_WAY for edge in migrations)


def test_the_real_registry_emits_only_the_routes_both_of_whose_ends_exist() -> None:
    registry = default_registry()

    assert registry.game_ids == [
        "diamond",
        "emerald",
        "firered",
        "leafgreen",
        "pearl",
        "platinum",
        "ruby",
        "sapphire",
    ]

    routes = [(edge.from_, edge.to) for edge in registry.edges]

    # Ten link cables between the five Generation 3 cartridges, three wireless trades between
    # the three Sinnoh games, and fifteen one-way Pal Park trips from each of the five into each
    # of the three.
    assert len(routes) == 10 + 3 + 15
    assert routes == sorted(routes)
    assert ("diamond", "pearl") in routes
    assert ("ruby", "diamond") in routes

    # What is waiting is the Johto half of Generation 4, which is not written yet.
    assert {edge.to for _, edge in registry.held_back_edges} == {"heartgold", "soulsilver"}


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
        assert partners == set(gba.CARTRIDGES) - {module.GAME_ID}


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


# --- FireRed and LeafGreen --------------------------------------------------------------------


def test_the_kanto_pair_are_two_games_that_name_each_other() -> None:
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID)).game
        for module in (firered, leafgreen)
    }

    assert sorted(both) == ["firered", "leafgreen"]
    assert both["firered"].pair_partner == "leafgreen"
    assert both["leafgreen"].pair_partner == "firered"
    assert both["firered"].title != both["leafgreen"].title


def test_the_kanto_pair_are_generation_3_cartridges_set_somewhere_else() -> None:
    for module in (firered, leafgreen):
        game = module.build(context(module.GAME_ID)).game

        # Everything a Hoenn cartridge says about itself, except the region.
        assert game.generation == 3
        assert game.region == "Kanto"
        assert game.national_dex_through == 386
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.release is GameRelease.CARTRIDGE


def test_each_of_the_kanto_pair_trades_with_every_other_cartridge_but_itself() -> None:
    for module in (firered, leafgreen):
        partners = {edge.to for edge in module.edges()}

        assert module.GAME_ID not in partners
        assert partners == set(gba.CARTRIDGES) - {module.GAME_ID}


def test_both_halves_show_the_same_kanto_dex() -> None:
    api = FakeApi([(1, "bulbasaur"), (151, "mew")])

    for module in (firered, leafgreen):
        data = module.build(context(module.GAME_ID, api))

        # The same entries and the same numbering. Only the game id differs.
        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "bulbasaur"),
            (151, "mew"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)

    # The 151-entry Kanto dex, which PokeAPI files FireRed and LeafGreen under along with Red
    # and Blue. Not the National Dex the games also have: that is what the entity's reach says.
    assert set(api.asked_for) == {"kanto"}


def test_the_kanto_pair_mark_what_only_the_other_half_keeps() -> None:
    api = FakeApi([(23, "ekans"), (27, "sandshrew")])

    reasons = {}
    for module in (firered, leafgreen):
        data = module.build(context(module.GAME_ID, api))
        reasons[module.GAME_ID] = {
            entry.target.species: entry.unobtainable_reason for entry in data.dex_entries
        }

    # Each half says the other half's name, and says a trade is the way round it.
    assert reasons["firered"]["ekans"] is None
    assert "LeafGreen only" in reasons["firered"]["sandshrew"]
    assert "trade one in" in reasons["firered"]["sandshrew"]

    assert reasons["leafgreen"]["sandshrew"] is None
    assert "FireRed only" in reasons["leafgreen"]["ekans"]


def test_the_kanto_exclusives_mirror_each_other_exactly() -> None:
    # A version pair is symmetric: seven each, and no species on both lists. A name that drifted
    # onto one side only would be a species nobody could get at all.
    assert len(firered.ONLY_ON_LEAFGREEN) == len(leafgreen.ONLY_ON_FIRERED) == 7
    assert set(firered.ONLY_ON_LEAFGREEN) & set(leafgreen.ONLY_ON_FIRERED) == set()


def test_the_kanto_pair_were_drawn_from_one_sheet_of_their_own() -> None:
    # One directory for the two of them, so the build fetches it once however many games name
    # it - and not the Hoenn sheet, which is a different set of drawings of the same generation.
    sets = {
        module.build(context(module.GAME_ID)).game.sprite_set for module in (firered, leafgreen)
    }

    assert sets == {"generation-iii/firered-leafgreen"}
    assert hoenn.PAIR_SPRITE_SET not in sets
    assert emerald.SPRITE_SET not in sets


def test_both_kanto_halves_say_the_same_thing_about_mew() -> None:
    # Neither cartridge has one, and neither pretends the other does.
    assert firered.UNOBTAINABLE["mew"] == leafgreen.UNOBTAINABLE["mew"] == kanto.MEW_REASON
    assert "mew" not in firered.ONLY_ON_LEAFGREEN
    assert "mew" not in leafgreen.ONLY_ON_FIRERED
    # Step 7: which distributions reached these cartridges, not the Generation 1 ones that put a
    # Mew on a Game Boy it can never leave.
    assert "2005" in kanto.MEW_REASON
    assert "1996" not in kanto.MEW_REASON


def test_step_seven_names_the_events_behind_the_kanto_exclusives() -> None:
    # An event does not make an entry obtainable. It answers the next question, which is where
    # one could ever have come from - and for thirteen of the fourteen exclusives there is one.
    covered = {
        species
        for table in (firered.ONLY_ON_LEAFGREEN, leafgreen.ONLY_ON_FIRERED)
        for species, event in table.items()
        if event is not None
    }

    assert len(covered) == 13
    # The exception, and it is a fact rather than a gap: nothing ever distributed one of these.
    assert firered.ONLY_ON_LEAFGREEN["pinsir"] is None
    assert "trade one in" in firered.UNOBTAINABLE["pinsir"]
    assert "handed one out" not in firered.UNOBTAINABLE["pinsir"]


def kanto_exclusive(pokemon: str, firered_rate: int, leafgreen_rate: int) -> dict:
    """One species on one route, at a different rate in each half of the pair."""
    return {
        pokemon: [
            {
                "location_area": {"name": "kanto-route-1-area"},
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
                    for version, rate in (
                        ("firered", firered_rate),
                        ("leafgreen", leafgreen_rate),
                    )
                ],
            }
        ]
    }


def test_each_kanto_half_reads_its_own_version_of_the_encounter_table() -> None:
    # The version is the whole difference between the two files, so it had better be the thing
    # that decides what comes out.
    for module, rate in ((firered, 25), (leafgreen, 65)):
        api = FakeApi(
            [(16, "pidgey")],
            kanto_exclusive("pidgey", firered_rate=25, leafgreen_rate=65),
        )

        wild = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "wild"
        ]

        assert [one.rate_percent for one in wild] == [rate]
        assert all(one.game == module.GAME_ID for one in wild)


def test_a_species_only_the_other_kanto_half_has_brings_no_slot() -> None:
    # Ekans is on FireRed and Sandshrew on LeafGreen. A cartridge that never meets one says so
    # by having nothing to say, not by inventing an empty slot.
    api = FakeApi(
        [(23, "ekans")],
        {
            "ekans": [
                {
                    "location_area": {"name": "kanto-route-4-area"},
                    "version_details": [
                        {
                            "version": {"name": "firered"},
                            "encounter_details": [
                                {
                                    "min_level": 6,
                                    "max_level": 12,
                                    "chance": 35,
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
        return [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "wild"
        ]

    assert len(wild_of(firered)) == 1
    assert wild_of(leafgreen) == []


def prize(pokemon: str, versions: tuple[str, ...]) -> dict:
    """One species in the Game Corner's window, in the versions given."""
    return {
        pokemon: [
            {
                "location_area": {"name": "celadon-city-prize-corner"},
                "version_details": [
                    {
                        "version": {"name": version},
                        "encounter_details": [
                            {
                                "min_level": 9,
                                "max_level": 9,
                                "chance": 100,
                                "method": {"name": "gift"},
                                "condition_values": [],
                            }
                        ],
                    }
                    for version in versions
                ],
            }
        ]
    }


def test_the_kanto_pair_name_who_hands_over_a_starter() -> None:
    api = FakeApi([(1, "bulbasaur")], prize("bulbasaur", ("firered", "leafgreen")))

    for module in (firered, leafgreen):
        gifts = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "gift"
        ]

        assert len(gifts) == 1
        # PokeAPI calls a starter, a fossil and a present from a stranger all "gift"; which of
        # the three this is, and whose hand it comes out of, are the game's own facts.
        assert gifts[0].gift_kind == GiftKind.STARTER
        assert gifts[0].npc == "Professor Oak"


def test_the_game_corner_charges_each_half_its_own_price() -> None:
    # The same Abra, two cartridges, two prices. It is the one table the pair disagree about in
    # more than which species stands in the window.
    api = FakeApi([(63, "abra")], prize("abra", ("firered", "leafgreen")))

    prices = {}
    for module in (firered, leafgreen):
        gifts = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "gift"
        ]
        prices[module.GAME_ID] = gifts[0].requirement

    assert "180 coins" in prices["firered"]
    assert "120 coins" in prices["leafgreen"]


def test_a_prize_only_one_half_sells_is_priced_for_that_half_alone() -> None:
    assert set(kanto.PRIZE_CORNER["scyther"]) == {"firered"}
    assert set(kanto.PRIZE_CORNER["pinsir"]) == {"leafgreen"}
    assert "scyther" not in kanto.gifts("leafgreen")
    assert "pinsir" not in kanto.gifts("firered")


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
