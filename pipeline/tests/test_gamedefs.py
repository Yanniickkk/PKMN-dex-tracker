"""What each game says about itself, and how the registry handles edges between games.

Phase 2 step 1 is exactly this: a game entity and the routes it brings. These pin what is easy
to get subtly wrong later - a dex source, a National Dex cap, an edge pointing at nothing.
"""

from __future__ import annotations

from datetime import date

import pytest

from livingdex_pipeline.build import default_registry
from livingdex_pipeline.gamedefs import (
    alola,
    alpha_sapphire,
    bank,
    black,
    black2,
    blue,
    crystal,
    diamond,
    ds,
    emerald,
    firered,
    gba,
    gbc,
    gen6,
    gold,
    heartgold,
    hoenn,
    home,
    johto,
    kalos,
    kanto,
    leafgreen,
    lets_go,
    lets_go_eevee,
    lets_go_pikachu,
    moon,
    omega_ruby,
    pearl,
    platinum,
    red,
    ruby,
    sapphire,
    silver,
    sinnoh,
    soulsilver,
    sun,
    unova,
    white,
    white2,
    x,
    y,
    yellow,
)
from livingdex_pipeline.games import BuildContext, GameRegistry
from livingdex_pipeline.gifts import GiftDetail
from livingdex_pipeline.models import (
    AllSpeciesFilter,
    DexSource,
    DexTarget,
    EncounterMethod,
    Form,
    FormKind,
    Game,
    GameData,
    GameRelease,
    GiftKind,
    PokemonType,
    PresentInTargetDexFilter,
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
    "red-blue": 1,
    "yellow": 2,
    "gold-silver": 3,
    "crystal": 4,
    "ruby-sapphire": 5,
    "emerald": 6,
    "firered-leafgreen": 7,
    "diamond-pearl": 8,
    "platinum": 9,
    "heartgold-soulsilver": 10,
    "black-white": 11,
    "black-2-white-2": 12,
    "x-y": 13,
    "omega-ruby-alpha-sapphire": 14,
    "sun-moon": 15,
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
        #: species -> extra (pokemon, is_default=False) pairs, for the tests that need one.
        self.extra_varieties: dict[str, list[tuple[str, bool]]] = {}

    def entries(self) -> list[tuple[int, str]]:
        """The fake dex, without recording that anybody asked for it."""
        return list(self._entries)

    def pokedex(self, name: str, *, refresh: bool = False) -> list[tuple[int, str]]:
        self.asked_for.append(name)
        return list(self._entries)

    def retrieved_on(self, url: str) -> date:
        """The day the cache says this url was fetched, which a citation carries."""
        return date(2026, 9, 21)

    def default_pokemon(self, species: str, *, refresh: bool = False) -> str:
        return species

    def varieties(self, species: str, *, refresh: bool = False) -> list[tuple[str, bool]]:
        """Every Pokemon of a species. The fakes hold one each unless a test says otherwise."""
        return [(self.default_pokemon(species), True), *self.extra_varieties.get(species, [])]

    def encounters(self, pokemon: str, *, refresh: bool = False) -> list:
        return self._encounters.get(pokemon, [])

    def evolution_chain(self, species: str, *, refresh: bool = False) -> str:
        return "treecko"

    def resource(self, path: str, *, refresh: bool = False) -> dict:
        if path.startswith("location-area/"):
            # Everywhere is Route 101, with one exception: the Friend Safari, which is the only
            # place in the dataset that asks something of a player before any of its slots can
            # be reached, and a gate is keyed by the place's name.
            area = path.removeprefix("location-area/")
            if area.startswith("friend-safari"):
                return {"location": {"name": "friend-safari"}}

            # And the Mirage spots, which are the one part of the Hoenn remakes' wild that
            # PokeAPI still answers for - and the one place a sub-area comes out of a slug.
            if area.startswith("mirage-spot-cave"):
                return {"location": {"name": "mirage-spot-cave"}}

            return {"location": {"name": "hoenn-route-101"}}

        if path.startswith("evolution-chain/"):
            return {"chain": TREECKO_CHAIN, "baby_trigger_item": None}

        if path.startswith("pokemon-species/"):
            # Only the day care asks for this, and only for the one thing PokeAPI knows that a
            # pair in it might not have: a species with no sexes needs a Ditto.
            return {"gender_rate": 4}

        if path.startswith("version-group/"):
            return {"order": VERSION_GROUP_ORDER[path.removeprefix("version-group/")]}

        if path == "location/friend-safari":
            return {"names": [{"language": {"name": "en"}, "name": "Friend Safari"}]}

        if path == "location/mirage-spot-cave":
            return {"names": [{"language": {"name": "en"}, "name": "Mirage Cave"}]}

        return {"names": [{"language": {"name": "en"}, "name": "Route 101"}]}


class FakeWiki:
    """Stands in for the client that reads a wiki page.

    Two shapes, because two generations read pages: one grotto for the Unova sequels and one
    location table for the Hoenn remakes. Every page it is asked for answers with both, which
    is enough for either game to build - what a parser does with a real page is
    :mod:`test_grottoes` and :mod:`test_encountertables`.

    ``in_omega_ruby`` and ``in_alpha_sapphire`` are the colours of the two games cells, because
    that is the only thing on a page that says which half of the pair a species is in. The
    Hoenn row is served on one page only - the remakes ask for sixty-nine - so a test counting
    records counts one.
    """

    def __init__(
        self,
        species: str,
        *,
        page: str = "Hoenn_Route_101",
        in_omega_ruby: bool = True,
        in_alpha_sapphire: bool = True,
    ) -> None:
        self.species = species
        self.page = page
        self.halves = (in_omega_ruby, in_alpha_sapphire)
        self.asked_for: list[str] = []

    def get_text(self, url: str, *, refresh: bool = False) -> str:
        self.asked_for.append(url)
        filled = "background:#303E51;"
        white = "background:#FFF;"
        omega, alpha = (filled if one else white for one in self.halves)
        here = url.endswith(f"/{self.page}")

        return (
            "<html><body><div id='mw-content-text'><h3>Route 2</h3><table><tbody>"
            "<tr><th>Pokémon</th><th>Games</th><th>Location</th>"
            "<th>Levels</th><th>Rate</th></tr>"
            f"<tr><td>{self.species}</td>"
            f"<th style='{filled}'>B2</th>"
            f"<th style='{filled}'>W2</th>"
            "<td>Hidden Grotto</td><td>55-59</td><td>1%</td></tr>"
            + (
                f"<tr><td>{self.species}</td>"
                f"<th style='{omega}'>OR</th>"
                f"<th style='{alpha}'>AS</th>"
                "<td>Grass</td><td>5-7</td><td>20%</td></tr>"
                if here
                else ""
            )
            + "</tbody></table></div></body></html>"
        )

    def retrieved_on(self, url: str) -> date:
        return date(2026, 9, 21)


def context(
    game_id: str,
    api: FakeApi | None = None,
    reaches: list[str] | None = None,
    wiki: FakeWiki | None = None,
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
        wiki=wiki or FakeWiki(listed[0]),
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
    for module in (diamond, pearl, platinum, heartgold, soulsilver):
        edges = module.edges()

        trades = {edge.to for edge in edges if edge.mechanism is TransferMechanism.TRADE}
        migrations = [edge for edge in edges if edge.mechanism is TransferMechanism.PAL_PARK]

        assert trades == set(ds.CARTRIDGES) - {module.GAME_ID}
        assert {edge.from_ for edge in migrations} == set(gba.CARTRIDGES)
        assert all(edge.to == module.GAME_ID for edge in migrations)
        assert all(edge.direction is TransferDirection.ONE_WAY for edge in migrations)


# --- HeartGold and SoulSilver -----------------------------------------------------------------


def test_the_johto_pair_are_two_games_that_name_each_other() -> None:
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID)).game
        for module in (heartgold, soulsilver)
    }

    assert sorted(both) == ["heartgold", "soulsilver"]
    assert both["heartgold"].pair_partner == "soulsilver"
    assert both["soulsilver"].pair_partner == "heartgold"
    assert both["heartgold"].title != both["soulsilver"].title


def test_the_johto_games_are_generation_4_cartridges_set_in_johto() -> None:
    for module in (heartgold, soulsilver):
        game = module.build(context(module.GAME_ID)).game

        assert game.generation == 4
        # Kanto is the second half of the map in both, and neither is a Kanto game.
        assert game.region == "Johto"
        assert game.national_dex_through == 493
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.released is not None


def test_johto_is_a_region_rather_than_a_generation() -> None:
    # Gold, Silver and Crystal are Johto too, and none of Generation 4 is true of them. So this
    # module carries the region and delegates the hardware, unlike `kanto`, which is written for
    # one generation and says so. A National Dex cap or a generation number appearing here is
    # the mistake this pins: it would be a fact about the DS pair written down as a fact about
    # the place.
    assert johto.REGION == "Johto"
    assert not hasattr(johto, "GENERATION")
    assert not hasattr(johto, "NATIONAL_DEX_THROUGH")

    # What it does know is how to put the region on a game, which is the one argument both
    # factories pass - the DS one below and the Generation 2 one beside it.
    assert (
        johto.ds_cartridge(
            game_id="heartgold",
            title="Pokémon HeartGold Version",
            version="HeartGold",
            released=date(2009, 9, 12),
            pair_partner="soulsilver",
        ).region
        == johto.REGION
    )


def test_gold_and_silver_are_the_same_region_on_other_hardware() -> None:
    # Two generations and ten years between them, one region. The entity says Johto for all
    # four, and everything the two sets disagree about - the dex, the routes, the hardware -
    # comes from their own generation's module rather than from this one.
    for module, partner in ((gold, "silver"), (silver, "gold")):
        game = module.build(context(module.GAME_ID)).game

        assert game.region == johto.REGION == "Johto"
        assert game.generation == 2
        assert game.pair_partner == partner
        assert game.release is GameRelease.VIRTUAL_CONSOLE
        # No National Dex behind the 251, as in Generation 1: this list is the whole goal.
        assert game.national_dex_through is None
        # The cartridge is 1999 in Japan and 2001 in Europe; the 3DS release is one day
        # everywhere, and it is the 3DS one this entity is.
        assert game.released == date(2017, 9, 22)

    assert heartgold.build(context("heartgold")).game.region == johto.REGION


def test_generation_2_numbers_by_the_national_dex_rather_than_by_johtos_own() -> None:
    # The surprise of step 2. Johto has a regional order and these games do list in it, but the
    # numbers they print are the old ones: a Gold player reads Chikorita as #152, not #001. An
    # entry carries one number and it is the one on the screen, so this dataset asks for the
    # national list and cuts it at Celebi.
    api = FakeApi([(1, "bulbasaur"), (152, "chikorita"), (251, "celebi"), (252, "treecko")])

    for module in (gold, silver, crystal):
        data = module.build(context(module.GAME_ID, api))

        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "bulbasaur"),
            (152, "chikorita"),
            (251, "celebi"),
        ]

    # Asked for the national list each time, and never for Johto's own.
    assert api.asked_for == ["national", "national", "national"]
    assert johto.ORIGINAL_DEX == "original-johto"

    # Which is not what the remake does: its regional numbers are what its player sees.
    assert (
        heartgold.build(context("heartgold", FakeApi([(1, "chikorita")]))).dex_entries[0].number
        == 1
    )


def generation_2_slot(
    area: str, versions: tuple[str, ...], *, time: str | None = None, method: str = "walk"
) -> list:
    """One encounter area as PokeAPI hands it over, in the Generation 2 versions given."""
    return [
        {
            "location_area": {"name": area},
            "version_details": [
                {
                    "version": {"name": version},
                    "encounter_details": [
                        {
                            "min_level": 2,
                            "max_level": 4,
                            "chance": 30,
                            "method": {"name": method},
                            "condition_values": [{"name": f"time-{time}"}] if time else [],
                        }
                    ],
                }
                for version in versions
            ],
        }
    ]


def test_generation_2_carries_the_time_of_day_its_slots_are_read_at() -> None:
    # The oldest games in the dataset to carry one, and nothing had to be written for it: the
    # condition vocabulary was filled in for HeartGold, which reads the same `time-night` off
    # the same field, and Generation 2 is where the clock was introduced in the first place.
    api = FakeApi(
        [(163, "hoothoot")],
        {"hoothoot": generation_2_slot("johto-route-29-area", ("gold", "silver"), time="night")},
    )

    [slot] = [
        one for one in gold.build(context("gold", api)).acquisition_methods if one.kind == "wild"
    ]

    assert slot.time_of_day == "night"
    assert slot.kind == "wild"


def test_each_johto_half_reads_its_own_version_of_the_encounter_table() -> None:
    # Gold has the Spinarak line and Silver the Ledyba one, which is the same switch every pair
    # in this dataset has. A game that never meets one says so by having nothing to say.
    api = FakeApi(
        [(165, "ledyba")],
        {"ledyba": generation_2_slot("johto-route-30-area", ("silver",))},
    )

    def wild_of(module) -> list:
        return [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "wild"
        ]

    assert len(wild_of(silver)) == 1
    assert wild_of(gold) == []


def test_crystal_is_a_third_version_and_closes_generation_2() -> None:
    game = crystal.build(context("crystal")).game

    assert game.pair_partner is None
    assert game.generation == 2
    assert game.region == johto.REGION
    assert game.release is GameRelease.VIRTUAL_CONSOLE
    assert game.national_dex_through is None
    # Five months after Gold and Silver's Virtual Console release, not a year after the
    # cartridge - the cartridge was December 2000 in Japan.
    assert game.released == date(2018, 1, 26)

    # It trades with both halves, which closes Generation 2's triangle the way Yellow closed
    # Generation 1's, and it opens a Time Capsule with none of them - that is Generation 1's
    # route, declared from the other end.
    assert {edge.to for edge in crystal.edges() if edge.mechanism is TransferMechanism.TRADE} == {
        "gold",
        "silver",
    }
    assert TransferMechanism.TIME_CAPSULE not in {edge.mechanism for edge in crystal.edges()}


def test_crystal_reads_the_generations_tables_without_being_asked() -> None:
    # Everything Gold and Silver's steps put in `gbc` and `johto` reaches this game for nothing,
    # which is the whole reason those two splits were drawn: the contest's ten hand-written
    # slots and the Tin Tower's name arrive with `gbc_acquisition_methods`, which never asks
    # which release it is building.
    api = FakeApi([(123, "scyther")])

    [slot] = [
        one
        for one in crystal.build(context("crystal", api)).acquisition_methods
        if one.kind == "wild"
    ]

    assert slot.location == "National Park"
    assert "Bug-Catching Contest" in slot.requirement
    assert slot.source.source == "bulbapedia"


def test_crystal_is_the_only_game_in_the_dataset_that_produces_a_celebi() -> None:
    # Three generations of games have had Celebi in their dex and none could fill it. This one
    # can, and only because it is modelled as the 3DS release: the GS Ball was Japan's alone on
    # the cartridge, and the Virtual Console release hands it over in every language.
    assert "GS Ball" in crystal.GIFTS["celebi"].requirement
    assert "Virtual Console" in crystal.GIFTS["celebi"].requirement

    # And the two games that cannot make one point at this one rather than at an event.
    assert "Crystal" in gold.UNOBTAINABLE["celebi"]
    assert "Crystal" in silver.UNOBTAINABLE["celebi"]
    # It is Crystal's own row rather than the generation's: the other two have nothing to say
    # about a Celebi except where one could be traded from.
    assert "celebi" not in johto.GBC_GIFTS


def test_the_day_care_is_breeding_even_where_pokeapi_calls_it_a_gift() -> None:
    # PokeAPI lists seven eggs at Route 34 for Crystal and none at all for Gold and Silver, and
    # Route 34 is the day care: what it describes is breeding. Taking them back out keeps all
    # three games saying the same thing about a Pichu, and the egg table names the parents a
    # player actually has to leave there.
    assert set(crystal.NOT_A_GIFT) == {
        "pichu",
        "cleffa",
        "igglybuff",
        "tyrogue",
        "smoochum",
        "elekid",
        "magby",
    }

    api = FakeApi(
        [(172, "pichu")],
        {"pichu": generation_2_slot("route-34-area", ("crystal",), method="gift-egg")},
    )

    built = crystal.build(context("crystal", api)).acquisition_methods
    [record] = [one for one in built if one.target.species == "pichu"]

    # Not the gift PokeAPI called it, but the breeding record that names what to leave there.
    assert record.kind == "breeding"
    assert list(record.parents) == [DexTarget(species="pikachu"), DexTarget(species="raichu")]


def test_crystal_offers_the_generations_seven_trades_and_one_of_its_own() -> None:
    # The only in-game trade in Generation 2 that is not in all three releases: a Xatu for a
    # Haunter, in the same house in Pewter City that trades the Rapidash.
    assert len(crystal.TRADES) == 8
    assert crystal.TRADES[:7] == johto.GBC_TRADES

    [extra] = [one for one in crystal.TRADES if one not in johto.GBC_TRADES]

    assert (extra.gets, extra.wants, extra.location) == ("xatu", "haunter", "Pewter City")
    # Its own version group too, which every third version in this dataset has had.
    assert crystal.VERSION_GROUP == "crystal"
    assert johto.GBC_PAIR_VERSION_GROUP == "gold-silver"


def test_crystal_writes_down_the_tyrogue_pokeapi_forgot() -> None:
    # The Karate King hands one over in all three releases and PokeAPI has the row for two of
    # them. Without it this game has no Tyrogue and therefore no Hitmon either - all three
    # evolve from it and nothing here hatches one - so the missing row closes a circle rather
    # than leaving a hole.
    [gift] = crystal.HANDED_OVER

    assert gift.species == "tyrogue"
    assert gift.npc == "The Karate King"
    assert "tyrogue" not in johto.GBC_EGGS

    api = FakeApi([(236, "tyrogue")])
    built = crystal.build(context("crystal", api)).acquisition_methods
    [record] = [one for one in built if one.target.species == "tyrogue"]

    assert record.kind == "gift"
    assert record.location == "Mt. Mortar, B1F"
    assert record.source.source == "bulbapedia"


def test_crystal_drops_five_things_where_a_third_version_usually_adds() -> None:
    # Yellow, Emerald and Platinum all add to the pair they follow. This one takes five away and
    # gives none of them back: Vulpix is Silver's, Mankey is Gold's, and Mareep, Girafarig and
    # Remoraid are in both halves and in no grass here.
    assert set(crystal.ELSEWHERE_IN_GENERATION_2) == {
        "vulpix",
        "mankey",
        "mareep",
        "girafarig",
        "remoraid",
    }
    assert crystal.UNOBTAINABLE["vulpix"] == johto.gbc_only_on("Silver")
    assert crystal.UNOBTAINABLE["mankey"] == johto.gbc_only_on("Gold")
    assert crystal.UNOBTAINABLE["mareep"] == johto.gbc_only_on("Gold and Silver")

    # Read off each species' own game-locations table rather than from PokeAPI's silence, which
    # is the lesson the legendary birds taught at Gold's step 7.
    assert all(event is None for _, event in crystal.ELSEWHERE_IN_GENERATION_2.values())


def test_the_third_version_is_the_only_one_that_can_fill_the_last_entry() -> None:
    # Fifteen here against seventeen in each half, and the two it does not share are the point.
    # Every Generation 2 release lacks the same ten; Celebi is the pair's eleventh and this
    # game's only source.
    assert len(crystal.UNOBTAINABLE) == 15
    assert len(gold.UNOBTAINABLE) == len(silver.UNOBTAINABLE) == 17

    assert set(johto.GBC_UNOBTAINABLE) <= set(crystal.UNOBTAINABLE)
    assert "celebi" not in crystal.UNOBTAINABLE
    assert "celebi" in gold.UNOBTAINABLE
    assert johto.GBC_PAIR_UNOBTAINABLE["celebi"] == johto.GBC_CELEBI_REASON


def test_the_bug_catching_contest_is_written_down_because_pokeapi_has_none_of_it() -> None:
    # The one part of these games PokeAPI carries nothing for, and it is not a detail: Scyther
    # and Pinsir are in no grass in either game, so a dataset without the contest says they
    # cannot be caught in Gold at all. Read off Bulbapedia and cited to it, which is what makes
    # these records tellable from every other slot in the dataset.
    api = FakeApi([(123, "scyther")])

    [slot] = [
        one for one in gold.build(context("gold", api)).acquisition_methods if one.kind == "wild"
    ]

    assert slot.location == "National Park"
    assert slot.levels.minimum == 13
    assert "Bug-Catching Contest" in slot.requirement
    assert slot.source.source == "bulbapedia"

    # Ten species, and the four that need it: Scyther and Pinsir in both games, Weedle in Gold
    # and Caterpie in Silver, each of which the other version has in its grass.
    assert len(johto.GBC_CONTEST) == 10
    assert {one.species for one in johto.GBC_CONTEST} >= {
        "scyther",
        "pinsir",
        "weedle",
        "caterpie",
    }


def test_generation_2_trades_seven_things_and_records_who_it_traded_with() -> None:
    # The first games in the dataset whose trades carry an original trainer: a Generation 1
    # trade says TRAINER and nothing else. Crystal adds an eighth of these and changes none;
    # the remake rearranged them, which is why the two tables are not one.
    assert len(johto.GBC_TRADES) == 7
    assert all(one.npc for one in johto.GBC_TRADES)

    pair = {(one.gets, one.wants) for one in johto.GBC_TRADES}
    remake = {(one.gets, one.wants) for one in johto.DS_PAIR_TRADES}

    # Blackthorn hands over a Rhydon here and a Dodrio there, for the same Dragonair.
    assert ("rhydon", "dragonair") in pair
    assert ("dodrio", "dragonair") in remake
    # And Xatu is Crystal's trade, so it is in neither of these.
    assert "xatu" not in {one.gets for one in johto.GBC_TRADES}


def test_generation_2_hatches_the_babies_it_invented_and_no_others() -> None:
    # Breeding starts here, and so do the babies that need it: six, none of them in any grass.
    # The remake's list is twice as long and every extra is a later generation reaching back -
    # five incense babies that do not exist yet, and Bonsly for a trade these games do not have.
    assert set(johto.GBC_EGGS) == {
        "pichu",
        "cleffa",
        "igglybuff",
        "smoochum",
        "elekid",
        "magby",
    }
    assert all(one.requirement is None for one in johto.GBC_EGGS.values())

    # And no parent these games have never heard of. HeartGold may hatch an Elekid from an
    # Electivire; here the only parent is the Electabuzz that existed at the time.
    parents = {name for one in johto.GBC_EGGS.values() for name in one.parents}

    assert "electivire" not in parents
    assert "magmortar" not in parents
    assert johto.GBC_EGGS["elekid"].parents == ("electabuzz",)


def test_generation_2_drew_all_251_three_times_over() -> None:
    # Every pair before these was drawn once: Ruby and Sapphire share a set, so do FireRed and
    # LeafGreen, HeartGold and SoulSilver, Red and Blue. Gold and Silver drew all 251 twice over
    # and Crystal a third time, so a sheet here belongs to a game rather than to a pair.
    gold_set = gold.build(context("gold")).game.sprite_set
    silver_set = silver.build(context("silver")).game.sprite_set
    crystal_set = crystal.build(context("crystal")).game.sprite_set

    assert gold_set == "generation-ii/gold/transparent"
    assert silver_set == "generation-ii/silver/transparent"
    assert crystal_set == "generation-ii/crystal/transparent"
    assert len({gold_set, silver_set, crystal_set}) == 3
    # Which is not how their own region's remake did it.
    assert (
        heartgold.build(context("heartgold")).game.sprite_set
        == soulsilver.build(context("soulsilver")).game.sprite_set
    )

    # Transparent in all three, for the reason Generation 1 gives: the default sheets carry no
    # alpha channel at all, so every sprite would arrive in a white box on a dark grid. Their
    # sizes do not even agree with each other - 40x40 for the pair, 56x56 for Crystal - which is
    # the reason to keep checking rather than assuming.
    for one in (gold_set, silver_set, crystal_set):
        assert one.endswith("/transparent")


def test_gold_and_silver_share_eleven_of_the_seventeen_they_cannot_produce() -> None:
    # A pair usually differs by six and agrees about everything else. These two also agree about
    # eleven they both lack, and all but one of the eleven is Kanto's: half of their map is a
    # region whose first partners nobody hands over, whose fossils nobody revives, and whose
    # four legendaries are standing nowhere at all.
    assert len(gold.UNOBTAINABLE) == len(silver.UNOBTAINABLE) == 17
    assert set(gold.UNOBTAINABLE) & set(silver.UNOBTAINABLE) == set(johto.GBC_PAIR_UNOBTAINABLE)
    assert len(johto.GBC_PAIR_UNOBTAINABLE) == 11

    assert gold.UNOBTAINABLE["bulbasaur"] == johto.GBC_KANTO_STARTERS
    assert "Pewter Museum" in gold.UNOBTAINABLE["omanyte"]
    assert silver.UNOBTAINABLE["articuno"] == johto.GBC_KANTO_LEGENDS
    assert silver.UNOBTAINABLE["mewtwo"] == johto.GBC_KANTO_LEGENDS

    # Ten of the eleven point at the same way in, which is the route the Generation 1 side
    # declared: the Time Capsule.
    from_generation_1 = [
        reason for species, reason in johto.GBC_PAIR_UNOBTAINABLE.items() if species != "celebi"
    ]

    assert all("Time Capsule" in reason for reason in from_generation_1)


def test_celebi_waits_for_crystal_rather_than_for_an_event() -> None:
    # Ten distributions between 2000 and 2003 and every one of them onto a cartridge, so these
    # releases get none of them - the same argument Red's Mew gets, one generation on. What is
    # different is that the exception is a game rather than an event: Crystal's Virtual Console
    # release turns on the GS Ball event that was Japan's alone, so the way in is a trade.
    assert gold.UNOBTAINABLE["celebi"] == silver.UNOBTAINABLE["celebi"] == johto.GBC_CELEBI_REASON
    assert "GS Ball" in johto.GBC_CELEBI_REASON
    assert "Crystal" in johto.GBC_CELEBI_REASON
    # And Mew's reason is Red's reasoning read from the other end of the Time Capsule.
    assert "2016" in johto.GBC_MEW_REASON
    assert "Time Capsule" in johto.GBC_MEW_REASON


def test_no_generation_2_exclusive_was_ever_handed_out_for_these_releases() -> None:
    # Twelve species, twelve *In events* tables, and not one Virtual Console distribution among
    # them. The only Generation 2 events at all were the Celebis and the Mews, and those went
    # onto cartridges.
    assert set(gold.ONLY_ON_SILVER) == {
        "vulpix",
        "meowth",
        "ledyba",
        "delibird",
        "skarmory",
        "phanpy",
    }
    assert set(silver.ONLY_ON_GOLD) == {
        "growlithe",
        "mankey",
        "spinarak",
        "gligar",
        "teddiursa",
        "mantine",
    }
    assert all(event is None for event in gold.ONLY_ON_SILVER.values())
    assert all(event is None for event in silver.ONLY_ON_GOLD.values())

    # And every earlier step took something off this list, which is why it is worked out last.
    # Ekans is the Goldenrod Game Corner's in Gold and Sandshrew is Silver's; Weedle and
    # Caterpie are both in the Bug-Catching Contest; Ariados evolves from a Spinarak that comes
    # over the link.
    assert "ekans" not in gold.UNOBTAINABLE
    assert "sandshrew" not in silver.UNOBTAINABLE
    assert "weedle" not in gold.UNOBTAINABLE
    assert "caterpie" not in silver.UNOBTAINABLE
    assert "ariados" not in silver.UNOBTAINABLE


def test_generation_2_calls_the_tower_what_its_own_players_call_it() -> None:
    # PokeAPI names a location after the newest game that has it, so Ho-Oh's home comes through
    # as the Bell Tower - which is HeartGold's name for it and not Gold's. The table lives with
    # the generation rather than with the region, because all three of these games say Tin Tower
    # and both Generation 4 ones say Bell Tower.
    assert gbc.RENAMED_PLACES == {"Bell Tower": "Tin Tower"}

    # It does not belong to the region: Johto keeps the same name in both generations and it is
    # the games that disagree about it. Crystal gets this for nothing when it arrives, because
    # everything set here reads its own generation's table.
    assert not hasattr(johto, "RENAMED_PLACES")


def test_the_pair_switch_in_gold_and_silver_is_a_wing_rather_than_a_species() -> None:
    # The neatest version difference in these two games, and it is not a Pokemon at all. Each
    # half's Radio Tower Director hands over one wing in the middle of the story, so Gold meets
    # Ho-Oh at level 40 while Silver meets Lugia there; the other bird waits behind an old man
    # in Pewter City, which is Kanto, which is after the Elite Four.
    gold_gifts = johto.gbc_gifts("gold")
    silver_gifts = johto.gbc_gifts("silver")

    assert "Radio Tower Director" in gold_gifts["ho-oh"].requirement
    assert "Pewter City" in gold_gifts["lugia"].requirement
    assert "Radio Tower Director" in silver_gifts["lugia"].requirement
    assert "Pewter City" in silver_gifts["ho-oh"].requirement

    # Everything else about the two tables is the same, which is what makes them a pair.
    assert {
        species: detail
        for species, detail in gold_gifts.items()
        if species not in ("ho-oh", "lugia")
    } == {
        species: detail
        for species, detail in silver_gifts.items()
        if species not in ("ho-oh", "lugia")
    }


def test_a_gift_handed_over_in_two_places_is_described_once_for_each() -> None:
    # Eevee is Bill's in Goldenrod and also 6666 coins in Celadon, and the two records should
    # not both say "Bill". The second description leaves `where` out and says nothing, so the
    # window keeps the price the encounter already carries.
    eevee = johto.GBC_GIFTS["eevee"]

    assert isinstance(eevee, tuple)
    assert [one.where for one in eevee] == ["Goldenrod City, Bills House", None]
    assert eevee[0].npc == "Bill"
    assert eevee[1] == GiftDetail()


def test_generation_2_does_not_declare_the_time_capsule_a_second_time() -> None:
    # It goes both ways and it is one route, so only one side may declare it - and that side is
    # Generation 1, because the limit on it is a fact about Generation 1: a Game Boy game has
    # nowhere to put a Chikorita. Declaring it here as well would hand the registry the same
    # route twice, the way Pal Park is left with the game that receives.
    theirs = {edge.mechanism for edge in gold.edges()}

    assert TransferMechanism.TIME_CAPSULE not in theirs
    assert theirs == {TransferMechanism.TRADE, TransferMechanism.POKE_TRANSPORTER}
    assert TransferMechanism.TIME_CAPSULE in {edge.mechanism for edge in red.edges()}

    # And what it does trade with is the other two of its own generation, Crystal included.
    assert {edge.to for edge in gold.edges() if edge.mechanism is TransferMechanism.TRADE} == {
        "silver",
        "crystal",
    }


def test_both_johto_halves_show_the_same_updated_johto_dex() -> None:
    api = FakeApi([(1, "chikorita"), (256, "celebi")])

    for module in (heartgold, soulsilver):
        data = module.build(context(module.GAME_ID, api))

        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "chikorita"),
            (256, "celebi"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)

    # Not "original-johto", which is Gold and Silver's 251. Both halves asked for the same one.
    assert api.asked_for == ["updated-johto", "updated-johto"]


def test_the_region_names_both_of_its_dexes_apart() -> None:
    # The five Generation 4 evolutions the updated one adds are filed behind what they evolve
    # from, so it is not the original with five at the back: everything from Yanmega on shifts,
    # and Celebi is #256 where Gold and Silver have it at #251. One constant called "the Johto
    # dex" would have been read as "they share a dex", which is exactly what they do not do.
    assert johto.ORIGINAL_DEX != johto.UPDATED_DEX
    assert johto.UPDATED_DEX == "updated-johto"


def test_each_johto_half_asks_about_its_own_version() -> None:
    # One function answers for both halves and each brings its own version name. A slot that
    # belongs to one of them must not turn up in the other.
    slots = {
        "location_area": {"name": "hoenn-route-101-area"},
        "version_details": [
            {
                "version": {"name": "heartgold"},
                "encounter_details": [
                    {
                        "min_level": 5,
                        "max_level": 5,
                        "chance": 10,
                        "method": {"name": "walk"},
                        "condition_values": [],
                    }
                ],
            }
        ],
    }
    api = FakeApi([(1, "sentret")], {"sentret": [slots]})

    caught = {
        module.GAME_ID: [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "wild"
        ]
        for module in (heartgold, soulsilver)
    }

    assert [one.target.species for one in caught["heartgold"]] == ["sentret"]
    assert caught["soulsilver"] == []


def test_a_johto_cartridge_asks_about_its_whole_living_dex_not_its_own_pokedex() -> None:
    # Kanto is half of these games and none of it is in their 256 entries. Asking only about
    # the regional dex is what once left everything outside it with nothing recorded against
    # it, in games that are full of it.
    slots = {
        "location_area": {"name": "hoenn-route-101-area"},
        "version_details": [
            {
                "version": {"name": "heartgold"},
                "encounter_details": [
                    {
                        "min_level": 5,
                        "max_level": 5,
                        "chance": 10,
                        "method": {"name": "walk"},
                        "condition_values": [],
                    }
                ],
            }
        ],
    }
    # Rattata is not in the fake Johto dex; the living dex reaches it anyway.
    api = FakeApi([(1, "sentret")], {"rattata": [slots]})

    caught = [
        one
        for one in heartgold.build(
            context("heartgold", api, reaches=["rattata"])
        ).acquisition_methods
        if one.kind == "wild"
    ]

    assert [one.target.species for one in caught] == ["rattata"]


def test_the_johto_pair_hand_over_the_same_things_from_one_table() -> None:
    # What the two halves disagree about - which of two the Game Corner sells, which legendary
    # sleeps in the Embedded Tower, what level a cover legendary is caught at - PokeAPI already
    # files per version, so none of it needs a switch in the table.
    assert johto.DS_PAIR_GIFTS["chikorita"].kind is GiftKind.STARTER
    assert johto.DS_PAIR_GIFTS["chikorita"].npc == "Professor Elm"
    # Three sets of first partners in one game, which no other game in the dataset does.
    givers = {johto.DS_PAIR_GIFTS[species].npc for species in ("chikorita", "bulbasaur", "treecko")}
    assert givers == {"Professor Elm", "Professor Oak", "Steven"}


def test_the_two_gifts_of_one_species_are_described_one_at_a_time() -> None:
    # Bill's Eevee and the Celadon Game Corner's are the same species and nothing else alike.
    bill, rest = johto.DS_PAIR_GIFTS["eevee"]

    assert bill.npc == "Bill"
    assert bill.where == "Goldenrod City, Bills House"
    # The other has nothing of its own: the coins it costs are in the encounter's conditions.
    assert rest == GiftDetail()


def test_the_johto_pair_share_ten_traders_and_one_of_them_names_no_price() -> None:
    wanted = {trade.gets: trade.wants for trade in johto.DS_PAIR_TRADES}

    assert len(johto.DS_PAIR_TRADES) == 10
    assert wanted["onix"] == "bellsprout"
    # Jasmine takes whatever is in the party, so there is nothing to put here.
    assert wanted["steelix"] is None
    # Four of the ten are characters a player already knows, which is HeartGold's doing.
    assert {"Brock", "Jasmine", "Lt. Surge", "Steven"} <= {
        trade.npc for trade in johto.DS_PAIR_TRADES
    }


def test_only_the_generation_4_babies_need_an_incense() -> None:
    # A Pikachu has always simply laid a Pichu; a Marill lays another Marill unless a parent is
    # holding a Sea Incense. Getting that backwards sends a player shopping for nothing.
    eggs = johto.DS_PAIR_EGGS

    assert eggs["pichu"].requirement is None
    assert eggs["magby"].requirement is None
    assert "Odd Incense" in (eggs["mime-jr"].requirement or "")
    assert "Rock Incense" in (eggs["bonsly"].requirement or "")
    # Azurill, Budew and Chingling are in Johto's own grass, so an egg is not the only way to
    # one and the table does not claim it is.
    assert not ({"azurill", "budew", "chingling"} & set(eggs))
    # And a Bonsly is only ever hatched here, which is what Brock's trade asks for.
    assert eggs["bonsly"].parents == ("sudowoodo",)


def test_each_johto_half_keeps_the_others_exclusives_out_of_reach() -> None:
    # A version pair does not have to be symmetrical, and this one is not: six one way, six the
    # other, and they became six the same day rather than at the same time.
    assert set(heartgold.ONLY_ON_SOULSILVER) == {
        "ledyba",
        "vulpix",
        "meowth",
        "delibird",
        "teddiursa",
        "skarmory",
    }
    assert set(soulsilver.ONLY_ON_HEARTGOLD) == {
        "spinarak",
        "growlithe",
        "mankey",
        "gligar",
        "phanpy",
        # The sixth was found by the pass that walks a game's own evolutions back to what
        # starts them. A Mantine surfaces on Route 41 in HeartGold and nowhere here, and this
        # half's only other route to one is a Mantyke - which hatches from a Mantine.
        "mantine",
    }
    # What is not on either list is as deliberate: an evolution whose base is on it needs no
    # line of its own, because `reach.spread_unobtainable` hands it the same sentence. Ledian
    # is caught nowhere in HeartGold either, and it comes from a Ledyba that comes over the link.
    assert "ledian" not in heartgold.UNOBTAINABLE
    assert "arcanine" not in soulsilver.UNOBTAINABLE


def test_the_two_the_series_hands_out_say_which_distributions_reached_these_games() -> None:
    for module in (heartgold, soulsilver):
        assert "Wi-Fi" in module.UNOBTAINABLE["mew"]
        # Celebi is more than a dex entry here: the event one is what puts the GS Ball in Ilex
        # Forest, so saying only "event only" would have left out half of what it does.
        assert "GS Ball" in module.UNOBTAINABLE["celebi"]


def test_the_only_event_that_ever_covered_an_exclusive_was_a_place_to_walk() -> None:
    # Eleven species, eleven *In events* tables, and one hit: not a Pokemon that was handed out
    # but a Pokewalker route that was. An empty finding is still a finding.
    assert "Pokewalker" in (heartgold.ONLY_ON_SOULSILVER["meowth"] or "")
    assert all(event is None for event in soulsilver.ONLY_ON_HEARTGOLD.values())


# --- Red and Blue -----------------------------------------------------------------------------


def test_the_kanto_pair_are_the_virtual_console_releases_and_not_the_cartridges() -> None:
    # A Game Boy cartridge trades with another Game Boy cartridge and reaches nothing else, so
    # what is caught on one can never join a living dex kept anywhere later. These releases can,
    # through Poke Transporter, and that route is the whole reason they are in the dataset. So
    # there is one Red, it is the 3DS one, and the entity says so rather than the id.
    for module in (red, blue):
        game = module.build(context(module.GAME_ID)).game

        assert game.release is GameRelease.VIRTUAL_CONSOLE
        assert game.released == date(2016, 2, 27)
        assert game.generation == 1
        assert game.region == "Kanto"
        assert "vc" not in module.GAME_ID


def test_generation_1_has_no_national_dex_behind_its_own() -> None:
    # The first games in this dataset with only one list. `national_dex_through` is what a
    # living dex here aims at, and for these it is the game's own dex - which is why it is None
    # and the dex source says so.
    game = red.build(context("red")).game

    assert game.national_dex_through is None
    assert game.dex_source is DexSource.GAME_DEX


def test_a_generation_1_release_brings_its_trades_its_time_capsule_and_bank() -> None:
    edges = {(edge.to, edge.mechanism): edge for edge in red.edges()}

    assert ("blue", TransferMechanism.TRADE) in edges
    assert ("yellow", TransferMechanism.TRADE) in edges
    # Both ways and limited to the first 151 in both directions. Forward that is no limit at
    # all; coming back it is the whole story, because a Chikorita has no place in a game that
    # has never heard of it.
    capsule = edges[("gold", TransferMechanism.TIME_CAPSULE)]
    assert capsule.direction is TransferDirection.BOTH_WAYS
    assert capsule.filter.to == 151
    # And the one route these releases exist for.
    transporter = edges[(bank.NODE, TransferMechanism.POKE_TRANSPORTER)]
    assert transporter.direction is TransferDirection.ONE_WAY


def test_kanto_is_a_region_rather_than_a_generation() -> None:
    # Red and Blue are Kanto and so are FireRed and LeafGreen, forty years of hardware apart.
    # A generation number or a National Dex cap appearing here would be a fact about one pair
    # written down as a fact about the place - the same mistake `johto` is pinned against.
    assert kanto.REGION == "Kanto"
    assert not hasattr(kanto, "GENERATION")
    assert not hasattr(kanto, "NATIONAL_DEX_THROUGH")
    # One dex for both pairs, which PokeAPI agrees with: the remake kept Red and Blue's order,
    # unlike Johto's, where 150 entries were renumbered.
    assert kanto.DEX == "kanto"


def test_every_kanto_game_shows_the_same_151_entries_in_the_same_order() -> None:
    # One dex for five games, which is the region's doing: Yellow rearranged half of what is in
    # Red and Blue and renumbered nothing, and FireRed and LeafGreen show the same list again.
    # Johto's remake renumbered 150 entries; Kanto's changed nothing, twice.
    api = FakeApi([(1, "bulbasaur"), (151, "mew")])

    for module in (red, blue, yellow, firered, leafgreen):
        data = module.build(context(module.GAME_ID, api))

        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "bulbasaur"),
            (151, "mew"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)

    assert api.asked_for == ["kanto"] * 5


def test_in_generation_1_the_kanto_dex_is_the_whole_living_dex() -> None:
    # In FireRed it is the game's own Pokedex and the National Dex arrives later, 386 deep. In
    # Red there is nothing behind it: 151 entries is the list and the goal at once.
    assert red.build(context("red")).game.national_dex_through is None
    assert yellow.build(context("yellow")).game.national_dex_through is None
    assert firered.build(context("firered")).game.national_dex_through == 386


def test_kantos_gifts_are_the_part_the_remake_left_alone() -> None:
    # The same three in Oak's lab, the same scientist on Cinnabar reviving the same fossil, the
    # same choice of one Hitmon in the same dojo. One table for four games, and each pair adds
    # only what is its own.
    assert kanto.SHARED_GIFTS.keys() <= kanto.GB_GIFTS.keys()
    assert kanto.SHARED_GIFTS.keys() <= kanto.GBA_PAIR_GIFTS.keys()
    assert kanto.GB_GIFTS["omanyte"] == kanto.GBA_PAIR_GIFTS["omanyte"]

    # One door opens differently, and it is the one at the end.
    assert "Elite Four" in (kanto.GB_GIFTS["mewtwo"].requirement or "")
    assert "Network Machine" in (kanto.GBA_PAIR_GIFTS["mewtwo"].requirement or "")
    # And the Hypno that frightened Lostelle is the remake's alone.
    assert "hypno" not in kanto.GB_GIFTS


def test_red_and_blue_need_no_table_for_what_the_game_corner_charges() -> None:
    # The remake needed one - PokeAPI carries no prices for it - but for these two the coins are
    # a condition on the encounter, and they differ in species as well as in price.
    assert "scyther" not in kanto.GB_GIFTS
    assert "pinsir" not in kanto.GB_GIFTS


def test_yellow_is_a_third_version_rather_than_half_of_a_pair() -> None:
    game = yellow.build(context("yellow")).game

    assert game.pair_partner is None
    assert game.release is GameRelease.VIRTUAL_CONSOLE
    # The cartridge followed Red and Blue by two years; the 3DS release came out the same day.
    assert game.released == red.build(context("red")).game.released
    # And it trades with both of them, which is what closes Generation 1's triangle.
    assert {edge.to for edge in yellow.edges() if edge.mechanism is TransferMechanism.TRADE} == {
        "red",
        "blue",
    }


def test_yellow_replaces_the_three_in_oaks_lab_rather_than_adding_to_them() -> None:
    # In Red the lab holds three and you take one, so the other two need a second cartridge. In
    # Yellow it holds a Pikachu, the three are scattered across Kanto in the hands of three
    # strangers, and a player ends up with all four without trading for any of them.
    assert kanto.GB_GIFTS["bulbasaur"].kind is GiftKind.STARTER
    assert kanto.GB_GIFTS["bulbasaur"].npc == "Professor Oak"

    assert yellow.GIFTS["pikachu"].kind is GiftKind.STARTER
    assert yellow.GIFTS["pikachu"].npc == "Professor Oak"
    # Not starters here, whatever they are everywhere else, and no two from the same person.
    starters = ("bulbasaur", "charmander", "squirtle")
    assert all(yellow.GIFTS[one].kind is None for one in starters)
    assert len({yellow.GIFTS[one].npc for one in starters}) == 3

    # And what it leaves alone, which is the rest of Kanto.
    assert yellow.GIFTS["eevee"] == kanto.SHARED_GIFTS["eevee"]
    assert yellow.GIFTS["mewtwo"] == kanto.GB_GIFTS["mewtwo"]


def test_yellows_game_corner_needs_no_table_either() -> None:
    # It charges differently from the pair's and stocks different species - Vulpix and
    # Wigglytuff for coins, and both Scyther and Pinsir where Red and Blue split them - and
    # none of that needs writing down: PokeAPI carries the coins as a condition.
    assert "vulpix" not in yellow.GIFTS
    assert "scyther" not in yellow.GIFTS
    assert "pinsir" not in yellow.GIFTS


def generation_1_slot(area: str, versions: tuple[str, ...], *, method: str = "walk") -> list:
    """One encounter area as PokeAPI hands it over, in the Generation 1 versions given."""
    return [
        {
            "location_area": {"name": area},
            "version_details": [
                {
                    "version": {"name": version},
                    "encounter_details": [
                        {
                            "min_level": 3,
                            "max_level": 6,
                            "chance": 25,
                            "method": {"name": method},
                            "condition_values": [],
                        }
                    ],
                }
                for version in versions
            ],
        }
    ]


def test_yellow_reads_its_own_encounter_table_rather_than_the_pairs() -> None:
    # The Pikachu in Viridian Forest is Red and Blue's. In Yellow the only Pikachu is the one
    # that will not stay in its ball, there is none in any grass anywhere, and the slots it does
    # have are not the ones the pair has - which is why it reads its own version.
    api = FakeApi(
        [(25, "pikachu"), (69, "bellsprout")],
        {
            "pikachu": generation_1_slot("viridian-forest-area", ("red", "blue")),
            "bellsprout": generation_1_slot("kanto-route-5-area", ("yellow",)),
        },
    )

    def wild_of(module) -> list[str]:
        return [
            one.target.species
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "wild"
        ]

    assert wild_of(yellow) == ["bellsprout"]
    assert wild_of(red) == ["pikachu"]


def test_each_generation_1_release_describes_what_it_hands_over_in_its_own_words() -> None:
    # One row in PokeAPI - bulbasaur, gift, Cerulean City - and two games that mean different
    # things by it. In Red it is the starter out of Oak's lab. In Yellow it is a girl's
    # Bulbasaur, handed over because the Pikachu walking behind you is well looked after, and
    # reading it as Oak's would be reading Red's Kanto into Yellow.
    api = FakeApi(
        [(1, "bulbasaur")],
        {"bulbasaur": generation_1_slot("cerulean-city-area", ("red", "yellow"), method="gift")},
    )

    def gift_of(module):
        [one] = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "gift"
        ]
        return one

    assert gift_of(red).gift_kind is GiftKind.STARTER
    assert gift_of(red).npc == "Professor Oak"

    assert gift_of(yellow).gift_kind is GiftKind.NPC_GIFT
    assert gift_of(yellow).npc == "A girl in a house in Cerulean City"


def test_the_real_registry_emits_only_the_routes_both_of_whose_ends_exist() -> None:
    registry = default_registry()

    assert registry.game_ids == [
        "alpha-sapphire",
        "bank",
        "black",
        "black-2",
        "blue",
        "crystal",
        "diamond",
        "emerald",
        "firered",
        "gold",
        "heartgold",
        "home",
        "leafgreen",
        "lets-go-eevee",
        "lets-go-pikachu",
        "moon",
        "omega-ruby",
        "pearl",
        "platinum",
        "red",
        "ruby",
        "sapphire",
        "silver",
        "soulsilver",
        "sun",
        "ultra-moon",
        "ultra-sun",
        "white",
        "white-2",
        "x",
        "y",
        "yellow",
    ]

    routes = [(edge.from_, edge.to) for edge in registry.edges]

    # Three link cables between the three Generation 1 releases and three between the three
    # Generation 2 ones; nine Time Capsules, each of the older three to each of the newer three;
    # ten between the five Generation 3 cartridges, ten wireless trades between the five
    # Generation 4 games, and twenty-five one-way Pal Park trips from each of the five into each
    # of the five. Then six trades between the four Generation 5 cartridges, and twenty one-way
    # Poke Transfers, from each Generation 4 cartridge into each of the four. Then six between
    # the four Generation 6 cartridges, which is the whole of that generation's trading: the two
    # remakes arrived and the four routes X and Y had been declaring into an empty space became
    # real without either of those files being touched.
    #
    # And then Bank, which is the eighteen that arrived with the node: ten Poke Transporter
    # trips, one from each Virtual Console release and each Generation 5 cartridge, and for each
    # of the four Generation 6 cartridges a deposit and a withdrawal. The deposit and the
    # withdrawal are two routes rather than one because Bank hands back less than it takes. And
    # one more with HOME: the way out of Bank, which goes nowhere else and comes back from
    # nowhere.
    #
    # Generation 7 is six trades between its four cartridges, as Generations 5 and 6 each were,
    # and eight more Bank edges - a deposit and a withdrawal for each of the four. The four
    # routes Sun and Moon spent a pair's worth of steps declaring into an empty space are real
    # now, and neither of those two files was touched to do it.
    #
    # And five for the Let's Go pair, which is every route those two have: the cable between the
    # halves, and for each half a deposit into HOME and a withdrawal back out. They declare six
    # between them and two of those are the one trade. Nothing else in the dataset reaches them
    # and they reach nothing else - no Bank, no cartridge, not even the generation they are in.
    assert len(routes) == 3 + 3 + 9 + 10 + 10 + 25 + 6 + 20 + 6 + 10 + 4 + 4 + 1 + 6 + 8 + 5
    assert len(routes) == 130
    assert routes == sorted(routes)
    assert ("blue", "red") in routes
    assert ("red", "yellow") in routes
    assert ("gold", "silver") in routes
    assert ("crystal", "gold") in routes
    assert ("diamond", "pearl") in routes
    assert ("ruby", "diamond") in routes

    # The Time Capsule is declared once, by the Generation 1 side, and it reaches forward.
    assert ("red", "crystal") in routes
    assert ("crystal", "red") not in routes

    # The four trades Black and White had been declaring into an empty space are here, which is
    # what registering the sequels was for: neither of the two older files was edited, and both
    # halves of each pair now reach both halves of the other.
    assert ("black", "black-2") in routes
    assert ("black-2", "white") in routes
    assert ("black-2", "white-2") in routes
    assert ("platinum", "white-2") in routes

    # And the same thing one generation later, which is what registering the remakes was for.
    # Held once, whichever end is asked: X declared this route a generation before its other
    # end existed.
    assert ("omega-ruby", "x") in routes
    assert ("alpha-sapphire", "omega-ruby") in routes

    # And a third time, in Generation 7. Both halves of each Alola pair reach both halves of the
    # other, and a cable between the pairs is the one that has to refuse something.
    assert ("sun", "ultra-sun") in routes
    assert ("moon", "ultra-sun") in routes
    assert ("ultra-moon", "ultra-sun") in routes
    [across] = [
        edge for edge in registry.edges if edge.from_ == "sun" and edge.to == "ultra-sun"
    ]
    assert across.filter.to == 802
    [within] = [
        edge for edge in registry.edges if edge.from_ == "ultra-moon" and edge.to == "ultra-sun"
    ]
    assert within.filter.filter == "all"
    # What is not here, and will never be: a remake and the game it remakes. No cable reaches a
    # Game Boy Advance cartridge from a 3DS, and the five-game route between them runs through
    # Bank rather than between the two of them.
    assert ("ruby", "omega-ruby") not in routes
    assert ("omega-ruby", "ruby") not in routes

    # The fourteen that had been waiting for Bank are here, and no file that declared one was
    # touched to light it: ten Transporter trips and the four Generation 6 deposits. The
    # fifteenth is Bank's own way out, which waited for HOME.
    assert ("red", "bank") in routes
    assert ("black-2", "bank") in routes
    assert ("x", "bank") in routes
    assert ("bank", "x") in routes
    assert ("bank", "home") in routes
    # And the route the window refuses is refused by the graph rather than by the edge: Bank
    # holds one edge back to each Generation 6 cartridge, and that edge says who may use it.
    [withdrawal] = [
        edge for edge in registry.edges if edge.from_ == "bank" and edge.to == "omega-ruby"
    ]

    assert (withdrawal.history.from_, withdrawal.history.to) == (3, 6)
    assert all(edge.history is None for edge in registry.edges if edge.to == "bank")

    # And nothing at all is waiting. Every route any of the thirty entries declares has both of
    # its ends in the dataset - the four Sun and Moon declared into an empty space were the last
    # of them, and registering Ultra Sun and Ultra Moon lit all four without either of those
    # files being touched.
    #
    # It has been true once before, when Bank and HOME closed the graph, and it stopped being
    # true the moment Generation 7 opened. It will stop being true again with Let's Go.
    assert registry.held_back_edges == []


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
    assert hoenn.FIFTH_CAMPAIGN.lower() in hoenn.gba_only_on("Ruby", hoenn.FIFTH_CAMPAIGN).lower()
    assert emerald.UNOBTAINABLE["jirachi"] == hoenn.GBA_JIRACHI_REASON


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
    assert hoenn.GBA_PAIR_VERSION_GROUP == "ruby-sapphire"
    assert emerald.POKEAPI_VERSION_GROUP == "emerald"


def test_the_pair_share_one_gift_table() -> None:
    # They agree about every species they both have, so the table is written once. A key the
    # other half never sees simply never matches.
    assert ruby.hoenn.GBA_PAIR_GIFTS is sapphire.hoenn.GBA_PAIR_GIFTS
    assert "groudon" not in ruby.hoenn.GBA_PAIR_GIFTS
    assert ruby.hoenn.GBA_PAIR_GIFTS["treecko"].npc == "Professor Birch"


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
    assert hoenn.GBA_PAIR_SPRITE_SET not in sets
    assert emerald.SPRITE_SET not in sets


def test_both_kanto_halves_say_the_same_thing_about_mew() -> None:
    # Neither cartridge has one, and neither pretends the other does.
    assert firered.UNOBTAINABLE["mew"] == leafgreen.UNOBTAINABLE["mew"] == kanto.GBA_MEW_REASON
    assert "mew" not in firered.ONLY_ON_LEAFGREEN
    assert "mew" not in leafgreen.ONLY_ON_FIRERED
    # Step 7: which distributions reached these cartridges, not the Generation 1 ones that put a
    # Mew on a Game Boy it can never leave.
    assert "2005" in kanto.GBA_MEW_REASON
    assert "1996" not in kanto.GBA_MEW_REASON


def test_the_mews_that_reached_the_virtual_console_are_not_the_famous_ones() -> None:
    # This is where modelling the 3DS release rather than the cartridge pays. The Mews of the
    # Nintendo tours and the shopping centres went onto Game Boy cartridges; a download is not
    # one of those. Two events were for these releases, and both are 2016.
    assert red.UNOBTAINABLE["mew"] == blue.UNOBTAINABLE["mew"] == kanto.GB_MEW_REASON
    assert "Virtual Console" in kanto.GB_MEW_REASON
    assert "2016" in kanto.GB_MEW_REASON
    # And the two pairs do not share a sentence: what reached one never reached the other.
    assert kanto.GB_MEW_REASON != kanto.GBA_MEW_REASON


def test_no_generation_1_exclusive_was_ever_handed_out_for_these_releases() -> None:
    # Twelve species, twelve *In events* tables, and not one Virtual Console distribution among
    # them: what they have is for Gold and Silver, for the Generation 3 games, or later. Only
    # Mew ever got a Virtual Console event at all, which makes the emptiness structural rather
    # than a gap somebody should go back and fill.
    assert set(red.ONLY_ON_BLUE) == {
        "sandshrew",
        "vulpix",
        "meowth",
        "bellsprout",
        "magmar",
        "pinsir",
    }
    assert set(blue.ONLY_ON_RED) == {
        "ekans",
        "oddish",
        "mankey",
        "growlithe",
        "scyther",
        "electabuzz",
    }
    assert all(event is None for event in red.ONLY_ON_BLUE.values())
    assert all(event is None for event in blue.ONLY_ON_RED.values())
    # Sandslash is caught nowhere in Red either, and it is not on the list: it evolves from a
    # Sandshrew that comes over the link.
    assert "sandslash" not in red.UNOBTAINABLE
    assert "arbok" not in blue.UNOBTAINABLE


def test_yellow_was_drawn_again_rather_than_reusing_the_pairs_sheet() -> None:
    # The same 151 Pokemon, drawn a second time for the same hardware, which is why this game
    # gets a sprite set of its own instead of pointing at Red and Blue's.
    sets = {module.build(context(module.GAME_ID)).game.sprite_set for module in (red, blue)}

    assert sets == {kanto.GB_PAIR_SPRITE_SET}
    assert yellow.SPRITE_SET not in sets

    # And both Generation 1 sheets are the transparent variant, for the reason the pair's
    # comment gives: the default sheets carry no alpha channel, so every sprite would arrive in
    # a white box on a dark grid. Noticed by Yannick on the published exe, at Red's step 6.
    assert yellow.SPRITE_SET.endswith("/transparent")
    assert kanto.GB_PAIR_SPRITE_SET.endswith("/transparent")


def test_yellow_swaps_seven_different_things_than_the_pair_swaps_nine() -> None:
    # Five of the same places and not one of the same trades. What the pair only ever gets from
    # an NPC goes with them: Jynx and Farfetch'd are Cerulean's and Vermilion's, both trades are
    # gone, and Yellow answers the second with wild ones on Routes 12 and 13.
    assert len(yellow.TRADES) == 7
    assert len(kanto.GB_PAIR_TRADES) == 9

    pair = {(one.gets, one.wants) for one in kanto.GB_PAIR_TRADES}
    theirs = {(one.gets, one.wants) for one in yellow.TRADES}

    assert pair & theirs == set()
    # One species is handed over in both, and even that one costs something else: the Mr. Mime
    # on Route 2 wants an Abra in the pair and a Clefairy here.
    got_in_both = {one.gets for one in kanto.GB_PAIR_TRADES} & {one.gets for one in yellow.TRADES}
    assert got_in_both == {"mr-mime"}
    assert {"jynx", "farfetchd"} <= {one.gets for one in kanto.GB_PAIR_TRADES}
    # Nobody is named in either table: Generation 1 writes "TRAINER" on everything it hands over.
    assert all(one.npc is None for one in yellow.TRADES)


def test_yellow_is_its_own_version_group_where_the_pair_shares_one() -> None:
    # Nothing evolves differently here, and it is still not `red-blue`: PokeAPI files Yellow on
    # its own, and a game that asked for the pair's group would be asking about another game.
    assert yellow.VERSION_GROUP == "yellow"
    assert kanto.GB_PAIR_VERSION_GROUP == "red-blue"


def test_yellow_loses_what_the_anime_had_no_use_for() -> None:
    # Not a version split: eight entries leave the game and come back nowhere. Team Rocket's own
    # - Ekans, Meowth, Koffing - and the whole Weedle line with them, plus Electabuzz, Magmar
    # and a Jynx that was never wild in the pair either, only ever an NPC's in Cerulean City.
    assert set(yellow.UNOBTAINABLE) == {
        "weedle",
        "ekans",
        "meowth",
        "koffing",
        "jynx",
        "electabuzz",
        "magmar",
        "mew",
    }
    assert yellow.UNOBTAINABLE["mew"] == kanto.GB_MEW_REASON
    # Each says which of the other two to trade from, and one half is not always the answer.
    assert yellow.UNOBTAINABLE["ekans"] == kanto.gb_only_on("Red")
    assert yellow.UNOBTAINABLE["meowth"] == kanto.gb_only_on("Blue")
    assert yellow.UNOBTAINABLE["weedle"] == kanto.gb_only_on("Red and Blue")
    # No Virtual Console distribution ever reached one of them, the way none reached the pair's.
    assert all(event is None for _, event in yellow.ELSEWHERE_IN_GENERATION_1.values())


def test_yellow_can_still_reach_a_raichu_it_cannot_make_itself() -> None:
    # The sharpest case in the generation. No grass in Yellow holds a Pikachu, and the one Oak
    # hands over refuses the Thunder Stone - but a Pikachu traded in is not that Pikachu and
    # evolves like any other, so Raichu is reachable and does not belong on the list. The same
    # reasoning keeps Kakuna, Arbok, Persian and Weezing off it.
    assert "raichu" not in yellow.UNOBTAINABLE
    assert "pikachu" not in yellow.UNOBTAINABLE
    for evolved in ("kakuna", "beedrill", "arbok", "persian", "weezing"):
        assert evolved not in yellow.UNOBTAINABLE


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
    assert set(kanto.GBA_PRIZE_CORNER["scyther"]) == {"firered"}
    assert set(kanto.GBA_PRIZE_CORNER["pinsir"]) == {"leafgreen"}
    assert "scyther" not in kanto.gba_gifts("leafgreen")
    assert "pinsir" not in kanto.gba_gifts("firered")


# --- Black and White --------------------------------------------------------------------------


def test_the_unova_pair_are_two_games_that_name_each_other() -> None:
    both = {module.GAME_ID: module.build(context(module.GAME_ID)).game for module in (black, white)}

    assert sorted(both) == ["black", "white"]
    assert both["black"].pair_partner == "white"
    assert both["white"].pair_partner == "black"
    assert both["black"].title != both["white"].title
    # The same day, as every pair in this dataset has been.
    assert both["black"].released == both["white"].released == date(2010, 9, 18)


def test_the_unova_games_are_generation_5_cartridges_reaching_genesect() -> None:
    for module in (black, white):
        game = module.build(context(module.GAME_ID)).game

        assert game.generation == 5
        assert game.region == "Unova"
        assert game.national_dex_through == 649
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.release is GameRelease.CARTRIDGE


def test_generation_5_keeps_its_region_and_its_generation_in_one_module() -> None:
    # Everywhere else these are two modules: `kanto` is pinned against carrying a generation
    # number and `ds` against carrying a region. Generation 5 never left Unova, so one module
    # carries both and there is no second one for it to disagree with.
    assert unova.REGION == "Unova"
    assert unova.GENERATION == 5
    assert not hasattr(ds, "REGION")


# --- Black 2 and White 2 ----------------------------------------------------------------------


def test_the_unova_sequels_are_a_pair_of_their_own() -> None:
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID)).game for module in (black2, white2)
    }

    assert sorted(both) == ["black-2", "white-2"]
    # Each names the other and neither names Black or White. That is the whole claim step 1
    # makes about the sequels: they are a second pair, not two more versions of the first.
    assert both["black-2"].pair_partner == "white-2"
    assert both["white-2"].pair_partner == "black-2"
    assert both["black-2"].title != both["white-2"].title
    assert both["black-2"].released == both["white-2"].released == date(2012, 6, 23)


def test_the_unova_sequels_are_generation_5_cartridges_drawn_from_the_same_sheet() -> None:
    for module in (black2, white2):
        game = module.build(context(module.GAME_ID)).game

        assert game.generation == 5
        assert game.region == "Unova"
        assert game.national_dex_through == 649
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.release is GameRelease.CARTRIDGE
        # Two years later and the same drawings: Generation 5 is the only one that never
        # redrew itself for a later release.
        assert game.sprite_set == unova.SPRITE_SET


def test_the_sequels_read_the_other_unova_dex() -> None:
    api = FakeApi([(0, "victini"), (300, "genesect")])

    for module in (black2, white2):
        entries = module.build(context(module.GAME_ID, api)).dex_entries

        assert [one.number for one in entries] == [0, 300]
        assert [str(one.target) for one in entries] == ["victini", "genesect"]
        assert all(one.game == module.GAME_ID for one in entries)

    # The sequels' list, not the pair's. Both halves ask for the same one, and neither half of
    # either pair ever asks for the other pair's.
    assert api.asked_for == [unova.B2W2_DEX, unova.B2W2_DEX]


def test_the_sequels_number_from_zero_like_the_pair_before_them() -> None:
    # Victini is #000 in all four Unova games. The dex around it is a different list in the
    # sequels, and the one thing the renumbering left alone is where it starts.
    entries = black2.build(context("black-2", FakeApi([(0, "victini"), (1, "snivy")]))).dex_entries

    assert entries[0].number == 0
    assert str(entries[0].target) == "victini"


def test_every_generation_5_cartridge_trades_with_every_other() -> None:
    # Six routes between four games, and each one is declared twice - once from each end -
    # because a cartridge names the whole set whether or not the others are built. The registry
    # collapses the pairs; what is checked here is that all four agree about the set.
    for module in (black, white, black2, white2):
        traded = {edge.to for edge in module.edges() if edge.mechanism is TransferMechanism.TRADE}

        assert traded == set(unova.CARTRIDGES) - {module.GAME_ID}


def unova_slot(
    version: str,
    method: str,
    *,
    chance: int = 20,
    conditions: list[str] | None = None,
    area: str = "unova-route-3-area",
) -> dict:
    return {
        "location_area": {"name": area},
        "version_details": [
            {
                "version": {"name": version},
                "encounter_details": [
                    {
                        "min_level": 14,
                        "max_level": 16,
                        "chance": chance,
                        "method": {"name": method},
                        "condition_values": [{"name": one} for one in (conditions or [])],
                    }
                ],
            }
        ],
    }


def unova_wild(module, api: FakeApi) -> list:
    """The slots one game reads out of the encounter tables.

    Hidden Grottoes are wild records too and are not in those tables: they come off a wiki
    page, they are :mod:`test_grottoes`, and the two sequels would otherwise carry one here
    that has nothing to do with what is being asked.
    """
    return [
        one
        for one in module.build(context(module.GAME_ID, api)).acquisition_methods
        if one.kind == "wild" and one.method is not EncounterMethod.HIDDEN_GROTTO
    ]


def test_each_unova_half_reads_its_own_version_of_the_encounter_table() -> None:
    # The version is the whole difference between the two files, so it had better be the thing
    # that decides what comes out.
    for module, rate in ((black, 20), (white, 45)):
        api = FakeApi(
            [(1, "audino")],
            {
                "audino": [
                    unova_slot("black", "walk", chance=20),
                    unova_slot("white", "walk", chance=45),
                ]
            },
        )

        wild = unova_wild(module, api)

        assert [one.rate_percent for one in wild] == [rate]
        assert all(one.game == module.GAME_ID for one in wild)


def test_each_of_generation_5s_own_spots_is_its_own_method() -> None:
    # Sixty-two of the species a player of Black can catch are only in one of these. Calling
    # them "another way" - which is what the dataset did before Unova arrived - leaves a third
    # of the game with no answer to "where do I find it", and dark grass called plain walking
    # is worse than vague: a Bisharp is not in the ordinary patch beside it.
    expected = {
        "dark-grass": EncounterMethod.DARK_GRASS,
        "grass-spots": EncounterMethod.RUSTLING_GRASS,
        "cave-spots": EncounterMethod.DUST_CLOUD,
        "surf-spots": EncounterMethod.RIPPLING_WATER,
        "bridge-spots": EncounterMethod.BRIDGE_SHADOW,
    }

    for method, expected_method in expected.items():
        api = FakeApi([(1, "audino")], {"audino": [unova_slot("black", method)]})
        wild = unova_wild(black, api)

        assert [one.method for one in wild] == [expected_method]
        assert all(one.method is not EncounterMethod.OTHER for one in wild)


def test_fishing_in_a_ripple_keeps_the_rod_and_says_where_it_is_cast() -> None:
    # The one method that means two things. The rod is the half a player can be missing, so the
    # slot stays a Super Rod slot; the water it is cast into would be lost without a sentence.
    api = FakeApi([(1, "relicanth")], {"relicanth": [unova_slot("black", "super-rod-spots")]})

    wild = unova_wild(black, api)

    assert [one.method for one in wild] == [EncounterMethod.SUPER_ROD]
    assert wild[0].requirement == "Cast into rippling water"


def test_a_method_that_means_two_things_keeps_the_conditions_on_the_row_as_well() -> None:
    # The sentence the method adds must not push out the sentence the row already carried.
    api = FakeApi(
        [(1, "relicanth")],
        {"relicanth": [unova_slot("black", "super-rod-spots", conditions=["swarm-yes"])]},
    )

    requirement = unova_wild(black, api)[0].requirement

    assert "Cast into rippling water" in requirement
    assert "swarming" in requirement


def unova_gift(version: str, method: str, level: int, area: str, conditions=None) -> dict:
    return {
        "location_area": {"name": area},
        "version_details": [
            {
                "version": {"name": version},
                "encounter_details": [
                    {
                        "min_level": level,
                        "max_level": level,
                        "chance": 100,
                        "method": {"name": method},
                        "condition_values": [{"name": one} for one in (conditions or [])],
                    }
                ],
            }
        ],
    }


class Placed(FakeApi):
    """A fake whose encounters happen in a place with a name, rather than in Route 101."""

    def __init__(self, entries, encounters, *, slug: str, name: str) -> None:
        super().__init__(entries, encounters)
        self._slug = slug
        self._name = name

    def resource(self, path: str, *, refresh: bool = False) -> dict:
        if path.startswith("location-area/"):
            return {"location": {"name": self._slug}}

        if path.startswith("location/"):
            return {"names": [{"language": {"name": "en"}, "name": self._name}]}

        return super().resource(path, refresh=refresh)


def test_each_sequel_reads_its_own_version_of_the_encounter_table() -> None:
    # The version is the whole difference between the two files here too, and the sequels read
    # a version name of their own rather than the pair's.
    for module, rate in ((black2, 25), (white2, 55)):
        api = FakeApi(
            [(1, "audino")],
            {
                "audino": [
                    unova_slot("black-2", "grass-spots", chance=25),
                    unova_slot("white-2", "grass-spots", chance=55),
                    # The pair's tables are in the same source and are not theirs to read.
                    unova_slot("black", "grass-spots", chance=99),
                ]
            },
        )

        wild = unova_wild(module, api)

        assert len(wild) == 1
        assert wild[0].rate_percent == rate


def test_the_forest_behind_the_dex_says_what_it_takes_to_get_there() -> None:
    # PokeAPI marks conditions on a row, so it can say "only while it is swarming" and has no
    # way of saying "only if you are allowed in here". The Nature Preserve's tables are
    # ordinary grass; the plane is the whole story, and it is not in the source at all.
    api = Placed(
        [(1, "kecleon")],
        {"kecleon": [unova_slot("black-2", "dark-grass", area="nature-sanctuary-area")]},
        slug="nature-sanctuary",
        name="Nature Sanctuary",
    )

    [record] = unova_wild(black2, api)

    # And the name is wrong in the source as well: "Nature Sanctuary" is the Japanese name
    # carried across, and no English player was ever shown it.
    assert record.location == "Nature Preserve"
    assert record.requirement is not None
    assert record.requirement.startswith("Only by plane from Mistralton City")
    assert "297" in record.requirement


def test_a_gated_place_and_a_gated_slot_read_as_one_sentence() -> None:
    # Two requirements on one record: the way in, and what the row itself asks for. The way in
    # comes first because it is the part a player cannot do anything about, and the second is
    # lowered into the sentence rather than starting a new one.
    api = Placed(
        [(1, "basculin")],
        {"basculin": [unova_slot("black-2", "super-rod-spots", area="nature-sanctuary-area")]},
        slug="nature-sanctuary",
        name="Nature Sanctuary",
    )

    [record] = unova_wild(black2, api)

    assert record.requirement is not None
    assert record.requirement.endswith(" and cast into rippling water")
    assert "and Cast into" not in record.requirement


def test_an_ungated_place_says_nothing_extra() -> None:
    api = Placed(
        [(1, "audino")],
        {"audino": [unova_slot("black-2", "grass-spots", area="unova-route-3-area")]},
        slug="unova-route-3",
        name="Route 3",
    )

    [record] = unova_wild(black2, api)

    assert record.location == "Route 3"
    assert record.requirement is None


def test_the_sequels_mark_twenty_they_cannot_fill() -> None:
    for module in (black2, white2):
        assert len(module.UNOBTAINABLE) == 7 + 13


def test_victini_and_genesect_swap_places_between_the_two_pairs() -> None:
    # The clearest thing step 7 found in this generation, and it only shows up if the games
    # column is read rather than the rows counted. Black and White were never offered a
    # Genesect in the West; the sequels were offered one over Wi-Fi five weeks after they came
    # out. And Victini is the mirror: the first pair had it behind a Wi-Fi pass the world could
    # reach, and exactly one Victini distribution ever named the sequels - in Japan, in
    # Japanese, for six weeks.
    assert "rather than the sequels" in unova.BW_UNOBTAINABLE["genesect"]
    assert "Plasma Genesect" in unova.B2W2_UNOBTAINABLE["genesect"]

    assert "Liberty Pass" in unova.BW_UNOBTAINABLE["victini"]
    sequels = unova.B2W2_UNOBTAINABLE["victini"]
    assert "Liberty Garden is not on the sequels' map" in sequels
    assert "every other Victini distribution was for the first pair" in sequels


def test_the_forces_of_nature_are_behind_another_game_rather_than_a_date() -> None:
    # Not a distribution that ended: the Pokemon Dream Radar is a 3DS download that sends into
    # these two cartridges and nowhere else, and it is the only source of any of the three here.
    # Every other entry in either pair's list is a door that shut; this one is a door nobody
    # has written yet.
    for species in ("tornadus", "thundurus", "landorus"):
        reason = unova.B2W2_UNOBTAINABLE[species]

        assert "Dream Radar" in reason
        assert "No distribution ever handed one out" in reason
        # And they are not in the first pair's list at all, because the first pair has them
        # roaming its own Unova.
        assert species not in unova.BW_UNOBTAINABLE

    # The third one waits on the other two, so the Radar is two steps back rather than one.
    assert "Tornadus and Thundurus in the party" in unova.B2W2_UNOBTAINABLE["landorus"]


def test_the_sequels_split_almost_twice_as_much_as_the_first_pair() -> None:
    # Seven each in Black and White, thirteen each here - and what grew is the part nobody
    # thinks of as a version exclusive: five whole families from older generations, none of
    # which the first pair disagreed about at all.
    assert len(black2.ELSEWHERE_IN_GENERATION_5) == 13
    assert len(white2.ELSEWHERE_IN_GENERATION_5) == len(black2.ELSEWHERE_IN_GENERATION_5)
    assert len(black.ELSEWHERE_IN_GENERATION_5) == 7

    older = {"numel", "camerupt", "skitty", "delcatty", "elekid", "electabuzz", "electivire"}
    assert older <= set(black2.ELSEWHERE_IN_GENERATION_5)
    assert not older & set(black.ELSEWHERE_IN_GENERATION_5)
    assert not older & set(white.ELSEWHERE_IN_GENERATION_5)

    # And still not Cottonee or Petilil, for the same reason as in the first pair: the game
    # hands each half the one it is missing, two years later and on a different route.
    both = set(black2.ELSEWHERE_IN_GENERATION_5) | set(white2.ELSEWHERE_IN_GENERATION_5)
    assert not {"cottonee", "petilil"} & both


def test_not_one_of_the_sequels_exclusives_was_ever_handed_out() -> None:
    # The opposite of the first pair, where all four legendaries had a distribution and every
    # one of them was aimed at the half that could not catch it. Here the cover legendary was
    # not covered either: every Reshiram and Zekrom giveaway named Black or White alone.
    assert "reshiram" in black2.ELSEWHERE_IN_GENERATION_5
    assert "zekrom" in white2.ELSEWHERE_IN_GENERATION_5

    for module in (black2, white2):
        assert all("handed one out" not in reason for reason in _exclusive_reasons(module))


def _exclusive_reasons(module) -> list[str]:
    return [module.UNOBTAINABLE[species] for species in module.ELSEWHERE_IN_GENERATION_5]


def test_a_version_exclusive_can_now_name_more_than_one_other_game() -> None:
    # Four cartridges in one generation, so "the other half has it" stopped being the whole
    # answer. Black's Zekrom is in White, as it always was, and in Black 2 as well - and Black
    # did not have to be edited for that to become true, only for the sentence to say so.
    assert black.UNOBTAINABLE["zekrom"].startswith("White and Black 2 only in Generation 5")
    assert white.UNOBTAINABLE["reshiram"].startswith("Black and White 2 only in Generation 5")
    assert black2.UNOBTAINABLE["reshiram"].startswith("Black and White 2 only in Generation 5")

    # Thundurus is the one that did not grow: the sequels have no Thundurus either.
    assert black.UNOBTAINABLE["thundurus"].startswith("White only in Generation 5")

    # And an exclusive the first pair never had names one game, because only one has it.
    assert black2.UNOBTAINABLE["numel"].startswith("White 2 only in Generation 5")


def test_the_sequels_evolve_by_their_own_version_group() -> None:
    # The same rules as the first pair, read under the sequels' name. Passing "black-white"
    # through would be claiming a rule nobody checked still held two years later, which is the
    # sort of thing that is right until it is not.
    assert unova.B2W2_VERSION_GROUP == "black-2-white-2"
    assert unova.B2W2_VERSION_GROUP != unova.BW_VERSION_GROUP

    api = FakeApi([(1, "treecko"), (2, "grovyle")])

    for module in (black2, white2):
        evolutions = [
            one
            for one in module.build(context(module.GAME_ID, api)).acquisition_methods
            if one.kind == "evolution"
        ]

        assert [one.target.species for one in evolutions] == ["grovyle"]


def test_the_pair_that_swaps_its_exclusives_does_it_again_two_years_later() -> None:
    # Dye does this in Nacrene City in the first pair; here it is two different people on Route
    # 4. So Cottonee and Petilil look like version exclusives in all four games and are not in
    # any of them, and step 7 has to know that before it writes either of them off.
    black_2 = unova.b2w2_trades("black-2")[0]
    white_2 = unova.b2w2_trades("white-2")[0]

    assert (black_2.wants, black_2.gets) == ("cottonee", "petilil")
    assert (white_2.wants, white_2.gets) == ("petilil", "cottonee")
    assert black_2.location == white_2.location == "Route 4"
    # Two traders rather than one who changes their mind, which is how the first pair did it.
    assert black_2.npc != white_2.npc
    assert unova.BW_DYE_TRADE["black"].npc == unova.BW_DYE_TRADE["white"].npc


def test_a_trader_the_first_pair_had_is_asking_for_the_opposite_thing() -> None:
    # Manny still stands on Route 7. In Black and White he hands over an Emolga for a Boldore;
    # here he wants the Emolga and gives the Gigalith a Boldore turns into. Reading the first
    # pair's table into the sequels would have had a player hand over the wrong Pokemon.
    before = next(one for one in unova.BW_SHARED_TRADES if one.npc == "Manny")
    after = next(one for one in unova.B2W2_SHARED_TRADES if one.npc == "Manny")

    assert (before.wants, before.gets) == ("boldore", "emolga")
    assert (after.wants, after.gets) == ("emolga", "gigalith")

    # And one that did not change at all, which is what makes the other one worth noticing.
    assert any(one.npc == "Lillian" and one.gets == "rotom" for one in unova.BW_SHARED_TRADES)
    assert any(one.npc == "Lillian" and one.gets == "rotom" for one in unova.B2W2_SHARED_TRADES)


def test_the_sequels_day_care_carries_most_of_what_is_missing() -> None:
    # Twenty-seven against the first pair's four, and it is one fact about Unova written large:
    # the grass is full of grown-ups from older generations and almost none of their young.
    for version in ("black-2", "white-2"):
        assert len(unova.b2w2_eggs(version)) == 27

    assert len(unova.BW_EGGS) == 4

    # The oldest version exclusive in the series, still opposite itself, and in these two games
    # neither caterpillar is in the grass at all - each half has the adult in one grotto.
    assert "weedle" in unova.b2w2_eggs("black-2")
    assert "caterpie" not in unova.b2w2_eggs("black-2")
    assert "caterpie" in unova.b2w2_eggs("white-2")
    assert "weedle" not in unova.b2w2_eggs("white-2")


def test_the_two_genderless_families_say_a_ditto_is_needed() -> None:
    # Every other baby in the table hatches from a pair. These two adults have no mate anywhere
    # in the game, so "leave a Golurk at the day care" is only half an instruction.
    for species in ("beldum", "golett"):
        requirement = unova.B2W2_EGGS[species].requirement
        assert requirement is not None and "Ditto" in requirement


def sequel_gifts(module, api: FakeApi) -> list:
    return [
        one
        for one in module.build(context(module.GAME_ID, api)).acquisition_methods
        if one.kind == "gift"
    ]


def test_the_sequels_hand_their_first_partner_over_at_a_different_desk() -> None:
    api = FakeApi([(1, "snivy")], {"snivy": [unova_gift("black-2", "gift", 5, "aspertia-city")]})

    [gift] = sequel_gifts(black2, api)

    assert gift.gift_kind is GiftKind.STARTER
    # Bianca, at a lookout in a town the first pair does not have. Juniper hands these three
    # over in Black and White, and two years later she is not the one doing it.
    assert gift.npc == "Bianca"
    assert unova.BW_GIFTS["snivy"].npc == "Professor Juniper"


def test_the_two_unova_fossils_stopped_being_a_choice_a_save_lives_with() -> None:
    # The same two species and the same one-or-the-other, and the opposite answer. The first
    # pair's other fossil never comes back, so one of Tirtouga and Archen waits for a trade;
    # here the one left behind turns up for sale, and both entries fill in a single save.
    first = unova.BW_GIFTS["tirtouga"].requirement
    sequels = unova.B2W2_GIFTS["tirtouga"].requirement

    assert first is not None and sequels is not None
    assert "stays with them" in first
    assert "Join Avenue" in sequels


def test_each_half_is_rewarded_one_key_and_has_to_be_sent_the_other() -> None:
    # Regirock, Regice and Registeel are in both games and neither game can produce all three:
    # catching Regirock hands over one key, and the other chamber's key is the other half's
    # reward. So two of the six entries need a second cartridge, and it is not a trade - what
    # crosses over is a key, through the Unova Link.
    black_2 = unova.b2w2_gifts("black-2")
    white_2 = unova.b2w2_gifts("white-2")

    assert "rewarded with the Iron Key" in black_2["regirock"].requirement
    assert "rewarded with the Iceberg Key" in white_2["regirock"].requirement

    assert "the reward for catching Regirock" in black_2["registeel"].requirement
    assert "Unova Link" in black_2["regice"].requirement

    # And the mirror, which is what makes it a pair rather than an exclusive.
    assert "the reward for catching Regirock" in white_2["regice"].requirement
    assert "Unova Link" in white_2["registeel"].requirement

    # The fourth asks for all three at once, so it needs the other cartridge either way.
    assert unova.B2W2_GIFTS["regigigas"].requirement is not None
    assert "whichever half this is" in unova.B2W2_GIFTS["regigigas"].requirement


def test_the_weekly_visitors_come_on_different_days_in_the_two_halves() -> None:
    # Two rows PokeAPI carries no condition on at all. A player who reads "Route 4, level 25"
    # and walks there on a Tuesday finds an empty route and no reason why.
    assert unova.b2w2_gifts("black-2")["jellicent"].requirement == "Every Monday"
    assert unova.b2w2_gifts("white-2")["jellicent"].requirement == "Every Thursday"

    # And the bird of prey each half keeps, which is the other half's exclusive.
    assert "mandibuzz" in unova.b2w2_gifts("black-2")
    assert "braviary" in unova.b2w2_gifts("white-2")
    assert "braviary" not in unova.b2w2_gifts("black-2")


def test_the_zorua_the_first_pair_could_not_reach_is_simply_handed_over_here() -> None:
    # The sharpest difference step 4 found between the two pairs. In Black and White it takes
    # an event Celebi that was distributed for the Generation 4 games and cannot be got today;
    # two years later a man in Driftveil City offers N's Zorua to anyone who asks.
    assert "zorua" in unova.BW_UNOBTAINABLE
    assert "event Celebi" in unova.BW_UNOBTAINABLE["zorua"]

    handed_over = unova.B2W2_GIFTS["zorua"]

    assert handed_over.npc is not None and "Rood" in handed_over.npc
    assert "zorua" not in unova.b2w2_gifts("black-2")["regigigas"].requirement


def test_the_swords_of_justice_are_left_to_say_where_they_are() -> None:
    # They moved out of their chambers onto three routes, nothing in the source conditions the
    # first row, and the page about all three says nothing about an order this time. The first
    # pair needed three sentences here; inventing them again would be writing down a rule that
    # was true of the other games.
    for species in ("cobalion", "terrakion", "virizion"):
        assert species in unova.BW_GIFTS
        assert species not in unova.B2W2_GIFTS


def unova_gifts(module, api: FakeApi) -> list:
    return [
        one
        for one in module.build(context(module.GAME_ID, api)).acquisition_methods
        if one.kind == "gift"
    ]


def test_both_unova_halves_hand_over_the_same_things_from_one_table() -> None:
    api = FakeApi([(1, "snivy")], {"snivy": [unova_gift("black", "gift", 5, "nuvema-town-area")]})

    gifts = unova_gifts(black, api)

    assert len(gifts) == 1
    # PokeAPI calls a starter, a fossil and a present from a stranger all "gift"; which of the
    # three this is, and whose hand it comes out of, are the game's own facts.
    assert gifts[0].gift_kind is GiftKind.STARTER
    assert gifts[0].npc == "Professor Juniper"
    # One table for both halves, and one description for all three of the box's occupants.
    assert {unova.BW_GIFTS[one] for one in ("snivy", "tepig", "oshawott")} == {
        unova.BW_GIFTS["snivy"]
    }


def test_the_monkey_a_player_is_given_depends_on_the_starter_they_picked() -> None:
    # The woman outside the Dreamyard hands over the one the player's own first partner beats,
    # and PokeAPI files all three with no condition at all - so without this table the dataset
    # would promise every player all three.
    wanted = {"pansage": "Tepig", "pansear": "Oshawott", "panpour": "Snivy"}

    for species, starter in wanted.items():
        api = FakeApi(
            [(1, species)],
            {species: [unova_gift("black", "gift", 10, "dreamyard-area")]},
        )

        gifts = unova_gifts(black, api)

        assert gifts[0].requirement == f"Only in a save that started with {starter}"


def test_a_revived_fossil_says_where_the_fossil_itself_comes_from() -> None:
    # PokeAPI's condition is the bare item - "Helix Fossil" - which tells a player nothing about
    # the one thing that is hard here: seven of the nine are one a day from a Worker in Twist
    # Mountain, and only after the story ends.
    api = FakeApi(
        [(1, "omanyte")],
        {
            "omanyte": [
                unova_gift(
                    "black", "gift", 25, "nacrene-city-nacrene-museum", ["item-helix-fossil"]
                )
            ]
        },
    )

    gifts = unova_gifts(black, api)

    assert gifts[0].gift_kind is GiftKind.FOSSIL
    assert "Twist Mountain" in gifts[0].requirement
    assert "Ghetsis" in gifts[0].requirement
    # And the two this generation brought are a choice instead of a queue.
    assert "Relic Castle" in unova.BW_GIFTS["tirtouga"].requirement


def test_every_static_in_unova_says_what_it_takes_to_reach_it() -> None:
    # Five of these stood with a place and a level and nothing else, because PokeAPI carries no
    # condition on their rows and the species pages of two other sources say only the place.
    # What was missing was the door: Cobalion is behind Surf, Terrakion and Virizion are behind
    # Cobalion, and the two that respawn say when.
    gates = {
        "cobalion": "Surf",
        "terrakion": "Cobalion",
        "virizion": "Cobalion",
        "kyurem": "first visit",
        "volcarona": "Ghetsis",
    }

    for species, expected in gates.items():
        described = unova.BW_GIFTS[species]

        assert described.kind is GiftKind.STATIC_ENCOUNTER
        assert expected in described.requirement

    # Nothing in the table is a static with no way in written down.
    statics = [
        one
        for one in unova.BW_GIFTS.values()
        if isinstance(one, GiftDetail) and one.kind is GiftKind.STATIC_ENCOUNTER
    ]
    assert all(one.requirement for one in statics)


def test_each_unova_half_is_traded_the_other_halfs_exclusive() -> None:
    # Dye swaps each half what its own grass does not hold, which means two of the six species
    # that look like version exclusives are not exclusive at all. Step 7 has to know that before
    # it writes anyone off - the Kanto pair's Banette is the mistake this prevents.
    traded = {
        module.GAME_ID: [
            one
            for one in module.build(context(module.GAME_ID)).acquisition_methods
            if one.kind == "trade"
        ]
        for module in (black, white)
    }

    black_gets = {one.target.species: one for one in traded["black"]}
    white_gets = {one.target.species: one for one in traded["white"]}

    assert black_gets["petilil"].wants.species == "cottonee"
    assert white_gets["cottonee"].wants.species == "petilil"
    assert black_gets["petilil"].npc == white_gets["cottonee"].npc == "Dye"

    # And the other four are the same in both halves, so five each.
    assert len(traded["black"]) == len(traded["white"]) == 5
    assert set(black_gets) - {"petilil"} == set(white_gets) - {"cottonee"}


def test_a_trade_that_is_only_open_in_one_season_says_so() -> None:
    # The first game in the dataset where the calendar closes a door rather than changing what
    # is behind it: the Munchlax trade is in Undella Town and only in summer.
    munchlax = next(
        one
        for one in black.build(context("black")).acquisition_methods
        if one.kind == "trade" and one.target.species == "munchlax"
    )

    assert munchlax.requirement == "Only in summer"
    assert munchlax.wants.species == "cinccino"


def test_the_unova_pair_evolve_by_their_own_version_group() -> None:
    api = FakeApi([(1, "treecko"), (2, "grovyle")])

    for module in (black, white):
        methods = module.build(context(module.GAME_ID, api)).acquisition_methods
        evolutions = [one for one in methods if one.kind == "evolution"]

        assert [one.target.species for one in evolutions] == ["grovyle"]

    # The two halves are one group, and it is the group that brought this generation's own
    # triggers - Karrablast and Shelmet, who evolve only by being traded for each other.
    assert unova.BW_VERSION_GROUP == "black-white"


def test_the_day_care_hatches_the_four_babies_whose_parents_live_here() -> None:
    # Unova's grass is full of grown-up Pokemon from earlier generations and empty of their
    # babies, which is the opposite of Sinnoh - so this pair hatches four where that one hatched
    # none. The other eleven babies are left out because nothing here produces a parent: a record
    # saying "hatch a Pichu" in a game with no Pikachu is the lie the dead-end rule watches for.
    eggs = [
        one for one in black.build(context("black")).acquisition_methods if one.kind == "breeding"
    ]

    assert {one.target.species for one in eggs} == {
        "cleffa",
        "igglybuff",
        "smoochum",
        "chingling",
    }
    assert all(one.location == "Route 3, Pokemon Day Care" for one in eggs)
    assert "pichu" not in unova.BW_EGGS

    # Three of the four are Generation 2's babies and need nothing; the fourth is Generation 4's
    # and hides behind an item that is not on sale until the National Pokedex opens.
    chingling = next(one for one in eggs if one.target.species == "chingling")
    assert "Pure Incense" in chingling.requirement
    assert all(one.requirement is None for one in eggs if one.target.species != "chingling")


def test_the_unova_pair_mark_what_only_the_other_half_keeps() -> None:
    api = FakeApi([(83, "solosis"), (80, "gothita"), (150, "zekrom"), (1, "snivy")])

    reasons = {
        module.GAME_ID: {
            entry.target.species: entry.unobtainable_reason
            for entry in module.build(context(module.GAME_ID, api)).dex_entries
        }
        for module in (black, white)
    }

    # Two games rather than one, since the sequels were written: what Black is missing is in
    # White, as it always was, and in White 2 as well.
    assert reasons["black"]["solosis"].startswith("White and White 2 only in Generation 5")
    assert reasons["white"]["gothita"].startswith("Black and Black 2 only in Generation 5")
    # And what this half does produce says nothing at all.
    assert reasons["black"]["snivy"] is None


def test_the_unova_exclusives_mirror_each_other_exactly() -> None:
    # Seven each, and neither list holds Cottonee or Petilil: Dye swaps each half the one its
    # own grass is missing, so two species that look exactly like exclusives are not. Reading
    # the encounter tables alone would have written both of them off.
    assert len(black.ELSEWHERE_IN_GENERATION_5) == len(white.ELSEWHERE_IN_GENERATION_5) == 7
    # Every one of them is in the pair partner, which is what makes it a pair. Some are in one
    # of the sequels as well, and that is named beside it rather than instead of it.
    assert all("White" in games for games, _ in black.ELSEWHERE_IN_GENERATION_5.values())
    assert all("Black" in games for games, _ in white.ELSEWHERE_IN_GENERATION_5.values())

    both = set(black.ELSEWHERE_IN_GENERATION_5) | set(white.ELSEWHERE_IN_GENERATION_5)
    assert "cottonee" not in both
    assert "petilil" not in both


def test_every_generation_5_giveaway_went_to_the_half_that_could_not_catch_it() -> None:
    # Generation 4's four exclusives had no distribution at all. Here the four legendaries each
    # had one, and every one of them was for the other half - the Milos Island Thundurus for
    # Black, which has the Tornadus, and Ash's Zekrom for Black, whose box has Reshiram on it.
    covered = {
        module.GAME_ID: {
            species: event
            for species, (_, event) in module.ELSEWHERE_IN_GENERATION_5.items()
            if event is not None
        }
        for module in (black, white)
    }

    assert set(covered["black"]) == {"thundurus", "zekrom"}
    assert set(covered["white"]) == {"tornadus", "reshiram"}
    assert "Milos Island" in covered["black"]["thundurus"]
    assert "Ash's Reshiram" in covered["white"]["reshiram"]

    # The ordinary five were never handed out anywhere, which is a finding rather than a gap.
    assert [
        species for species, (_, event) in black.ELSEWHERE_IN_GENERATION_5.items() if event is None
    ] == ["solosis", "duosion", "reuniclus", "rufflet", "braviary"]


def test_the_six_neither_half_reaches_say_which_door_was_shut() -> None:
    # None of these is missing because the cartridge never held it. Each one is in the game,
    # behind a giveaway that has ended - which is the opposite of Mew in Kanto or Manaphy in
    # Sinnoh, where nothing in the game produced one at all.
    reasons = unova.BW_UNOBTAINABLE

    assert set(reasons) == {"victini", "zorua", "zoroark", "keldeo", "meloetta", "genesect"}
    assert "Liberty Pass" in reasons["victini"]
    assert "event Celebi" in reasons["zorua"]
    # Zorua is the one entry in the six that no distribution anywhere ever covered: what was
    # handed out was the key rather than the Pokemon.
    assert "No distribution ever handed out a Zorua" in reasons["zorua"]
    # And Genesect is the one where reading the games column mattered: it was handed out
    # plenty, and in the West every one of those was for the sequels.
    assert "rather than the sequels" in reasons["genesect"]


def test_both_unova_halves_count_thirteen_they_cannot_fill() -> None:
    for module in (black, white):
        assert len(module.UNOBTAINABLE) == 6 + 7


FOUR = (black, white, black2, white2)


def test_all_four_generation_5_games_were_drawn_from_one_sheet() -> None:
    # New in this generation: Platinum redrew Diamond and Pearl's sprites and HeartGold redrew
    # Generation 4's again, but the Unova sequels reuse these exactly - so one set answers for
    # four games, and the build fetches it once.
    sets = {module.build(context(module.GAME_ID)).game.sprite_set for module in FOUR}

    # One set, named after the pair that was drawn first, and the sequels two years later use
    # it unchanged. Nothing before this generation managed that: Platinum redrew Diamond and
    # Pearl's sprites and HeartGold redrew Generation 4's again. So the build fetches 649
    # pictures once and four games point at them.
    assert sets == {unova.SPRITE_SET}
    assert unova.SPRITE_SET == "generation-v/black-white"
    # Not the `transparent` variant Generations 1 and 2 needed: these sprites are already cut
    # out, and there is no such folder to ask for.
    assert not unova.SPRITE_SET.endswith("transparent")
    # And not the animated one beside it, which is the thing these games are famous for and is
    # a folder of GIFs the grid has nowhere to play.
    assert "animated" not in unova.SPRITE_SET

    # All four reach the same distance into it, which is why one fetch covers them: a set is
    # asked for as far as the game's National Dex goes, and Generation 5 stops at Genesect in
    # every one of the four.
    reach = {module.build(context(module.GAME_ID)).game.national_dex_through for module in FOUR}

    assert reach == {unova.NATIONAL_DEX_THROUGH} == {649}


def test_the_three_that_wait_on_a_distribution_bring_no_record_at_all() -> None:
    # Victini needs the Liberty Pass, Zorua the event Celebi, Zoroark a shiny event beast. All
    # three are really in the game, and all three are behind a giveaway that ended - so the
    # honest answer is step 7's sentence rather than a tile pointing at Liberty Garden.
    for species, area in (
        ("victini", "liberty-garden-lighthouse-basement"),
        ("zorua", "castelia-city-game-freak-hq-1f"),
        ("zoroark", "lostlorn-forest-area"),
    ):
        api = FakeApi([(1, species)], {species: [unova_gift("black", "static", 15, area)]})

        assert unova_gifts(black, api) == []


def test_one_encounter_filed_twice_is_kept_once() -> None:
    # PokeAPI has the Friday Musharna in the Dreamyard and in its basement, and only the first
    # row carries the conditions. Bulbapedia has one Musharna, in the basement - so the place is
    # dropped rather than the species, which still keeps its real row.
    api = Placed(
        [(1, "musharna")],
        {
            "musharna": [
                unova_gift("black", "static", 50, "dreamyard-area", ["weekday-friday"]),
                unova_gift("black", "static", 50, "dreamyard-b1f"),
            ]
        },
        slug="dreamyard",
        name="Dreamyard",
    )

    gifts = unova_gifts(black, api)

    assert len(gifts) == 1
    assert gifts[0].location.endswith("B1F")
    assert "Friday" in gifts[0].requirement


def test_the_forces_of_nature_are_put_back_in_the_region_they_roam() -> None:
    # PokeAPI files the roaming Tornadus in the Team Flare Secret HQ, which is in Kalos and is
    # not a place either of these games has. The same correction the Bell Tower needed, for a
    # different fault in the source.
    api = Placed(
        [(1, "tornadus")],
        {"tornadus": [unova_gift("black", "static", 40, "team-flare-secret-hq-area")]},
        slug="team-flare-secret-hq",
        name="Team Flare Secret HQ",
    )

    gifts = unova_gifts(black, api)

    assert gifts[0].location == "Roaming Unova"
    assert "Legend Badge" in gifts[0].requirement


def test_unova_is_the_first_region_whose_slots_carry_a_season() -> None:
    # Four tables where every game before had one. The field has been in the schema since
    # Phase 0 and empty in all sixteen games until now.
    api = FakeApi(
        [(1, "deerling")],
        {"deerling": [unova_slot("black", "walk", conditions=["season-winter"])]},
    )

    wild = unova_wild(black, api)

    assert wild[0].season == "winter"
    # It has a column of its own, so it does not also turn up in the sentence.
    assert wild[0].requirement is None


def test_both_unova_halves_show_the_same_dex_and_it_is_the_pairs_own() -> None:
    api = FakeApi([(0, "victini"), (155, "genesect")])

    for module in (black, white):
        entries = module.build(context(module.GAME_ID, api)).dex_entries

        assert [one.number for one in entries] == [0, 155]
        assert [str(one.target) for one in entries] == ["victini", "genesect"]
        assert all(one.game == module.GAME_ID for one in entries)

    # The pair's list, not the sequels'. Both halves ask for the same one.
    assert api.asked_for == [unova.BW_DEX, unova.BW_DEX]


def test_the_unova_dex_starts_at_zero_where_every_other_dex_starts_at_one() -> None:
    # Victini is #000 in these games, and the grid prints three digits, so a player sees the
    # number the game showed them. Nothing in the dataset had a zero before this.
    entries = black.build(context("black", FakeApi([(0, "victini"), (1, "snivy")]))).dex_entries

    assert entries[0].number == 0
    assert str(entries[0].target) == "victini"


def test_the_region_names_its_two_dexes_apart() -> None:
    # Black 2 and White 2 keep twelve of these numbers and renumber the rest, so the two lists
    # disagree about what nearly every number means - as Johto's two do, and unlike Platinum's,
    # which is the pair's with more at the end. One constant called DEX would be a lie here.
    assert unova.BW_DEX == "original-unova"
    assert unova.B2W2_DEX == "updated-unova"
    assert unova.BW_DEX != unova.B2W2_DEX


def test_each_unova_cartridge_trades_with_the_sequels_it_never_shipped_beside() -> None:
    trades = [edge for edge in black.edges() if edge.mechanism is TransferMechanism.TRADE]

    assert {edge.to for edge in trades} == {"white", "black-2", "white-2"}
    assert all(edge.direction is TransferDirection.BOTH_WAYS for edge in trades)
    assert all(isinstance(edge.filter, AllSpeciesFilter) for edge in trades)
    # Black named all three two years before the sequels existed and was not edited when they
    # arrived: the registry held those two back and let them through on their own. What this
    # asserts now is the other end of that - nothing Black declares is still waiting.
    assert not {edge.to for edge in trades} - set(default_registry().game_ids)


def test_no_generation_4_cartridge_claims_the_poke_transfer_itself() -> None:
    # The same reasoning as Pal Park: it is one way, and its National Dex limit is a fact about
    # the game that receives.
    for module in (diamond, pearl, platinum, heartgold, soulsilver):
        assert all(edge.mechanism is not TransferMechanism.POKE_TRANSFER for edge in module.edges())


def test_the_poke_transfer_takes_all_five_generation_4_games_and_stops_where_they_do() -> None:
    receiving = [
        edge for edge in white.edges() if edge.mechanism is TransferMechanism.POKE_TRANSFER
    ]

    assert {edge.from_ for edge in receiving} == set(ds.CARTRIDGES)
    assert all(edge.to == "white" for edge in receiving)
    assert all(edge.direction is TransferDirection.ONE_WAY for edge in receiving)
    # The cap is the sending generation's rather than this one's: nothing above Arceus existed
    # to be transferred, and the 156 species these games added never went the other way.
    assert all(edge.filter.to == 493 for edge in receiving)


def test_the_route_to_bank_is_one_route_the_cartridges_and_the_3ds_releases_share() -> None:
    # Poke Transporter shipped in 2013 for these four and was given the Virtual Console releases
    # three years later, so it belongs to neither side and both ask `bank` for it.
    for game_id, module in (("black", black), ("white", white), ("red", red), ("crystal", crystal)):
        assert bank.transporter_edge(game_id) in module.edges()


# --- X and Y ----------------------------------------------------------------------------------


def test_the_kalos_pair_are_two_games_that_name_each_other() -> None:
    both = {module.GAME_ID: module.build(context(module.GAME_ID)).game for module in (x, y)}

    assert sorted(both) == ["x", "y"]
    assert both["x"].pair_partner == "y"
    assert both["y"].pair_partner == "x"
    assert both["x"].title != both["y"].title
    # The same day, as every pair in this dataset has - and for the first time the same day
    # everywhere, rather than a Japanese date this file keeps and a player never saw.
    assert both["x"].released == both["y"].released == date(2013, 10, 12)


def test_the_kalos_pair_are_generation_6_cartridges_reaching_volcanion() -> None:
    for module in (x, y):
        game = module.build(context(module.GAME_ID)).game

        assert game.generation == 6
        assert game.region == "Kalos"
        assert game.national_dex_through == 721
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.release is GameRelease.CARTRIDGE


def test_the_kalos_pair_show_three_pokedexes_and_every_entry_says_which() -> None:
    # The first game in the series with more than one regional list, and the reason `DexEntry`
    # has a dex name at all. Central, Coastal and Mountain Kalos share no species and each
    # starts at #001, so an entry that does not name its list is not a fact about anything.
    api = FakeApi([(1, "chespin"), (2, "quilladin")])
    entries = x.build(context("x", api)).dex_entries

    assert api.asked_for == ["kalos-central", "kalos-coastal", "kalos-mountain"]
    assert [one.dex for one in entries] == [
        "Central Kalos",
        "Central Kalos",
        "Coastal Kalos",
        "Coastal Kalos",
        "Mountain Kalos",
        "Mountain Kalos",
    ]
    # Numbering restarts with each list rather than running on, which is what the games do and
    # what nothing in this dataset could say before now.
    assert [one.number for one in entries] == [1, 2, 1, 2, 1, 2]
    assert all(one.game == "x" for one in entries)


def test_the_three_lists_are_in_the_order_a_player_is_handed_them() -> None:
    # Lumiose City, then Ambrette Town, then Anistar. Not alphabetical and not by size: the
    # file's order is what the switch in the app offers, so it should be the order a player
    # already knows.
    assert [name for _, name in kalos.DEXES] == ["Central Kalos", "Coastal Kalos", "Mountain Kalos"]
    assert kalos.DEX_TOTAL == 457


def test_both_halves_of_the_kalos_pair_show_the_same_three_lists() -> None:
    api = FakeApi([(1, "chespin")])
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID, api)).dex_entries for module in (x, y)
    }

    assert [(one.dex, one.number) for one in both["x"]] == [
        (one.dex, one.number) for one in both["y"]
    ]
    assert api.asked_for == [dex for dex, _ in kalos.DEXES] * 2


def test_a_game_with_one_pokedex_does_not_name_it() -> None:
    # Twenty games were written before the field existed and none of them needs it: a number
    # that can only belong to one list does not have to say which. The field is written out
    # only where it decides something.
    entries = black.build(context("black")).dex_entries

    assert entries
    assert all(one.dex is None for one in entries)


def test_kalos_outlives_its_generation_and_the_modules_are_split_for_it() -> None:
    # Legends: Z-A is Lumiose City on the Switch, three generations after X and Y, so Kalos is
    # the second region in this dataset whose games are not all from one generation - Johto was
    # the first. The region module carries no generation and the generation module no region,
    # which is what stops a fact about Bank or a National Dex cap from being handed to a game
    # that has neither.
    assert kalos.REGION == "Kalos"
    assert not hasattr(kalos, "GENERATION")
    assert gen6.GENERATION == 6
    assert not hasattr(gen6, "REGION")
    # Named for the generation rather than called `cartridge`, so Z-A's factory can sit beside
    # this one instead of replacing it.
    assert not hasattr(kalos, "cartridge")


def test_every_generation_6_cartridge_trades_with_every_other() -> None:
    # Six routes between four games, declared from both ends, the way Generation 5's are. X and
    # Y named the two remakes for a whole generation before either existed; the registry held
    # those edges back, and adding the remakes let them through without those files changing.
    for module in (x, y, omega_ruby, alpha_sapphire):
        traded = {edge.to for edge in module.edges() if edge.mechanism is TransferMechanism.TRADE}

        assert traded == set(gen6.CARTRIDGES) - {module.GAME_ID}

    assert {"omega-ruby", "alpha-sapphire"} <= set(default_registry().game_ids)


def test_nothing_carries_an_older_cartridge_into_generation_6() -> None:
    # Every generation since the third has had one: Pal Park, then the Poke Transfer. This one
    # has no slot to put a cartridge in, and what replaces both is Bank - which is not a game,
    # and so not a route between two of them.
    for module in (x, y, omega_ruby, alpha_sapphire):
        mechanisms = {edge.mechanism for edge in module.edges()}

        assert TransferMechanism.PAL_PARK not in mechanisms
        assert TransferMechanism.POKE_TRANSFER not in mechanisms
        assert TransferMechanism.POKE_TRANSPORTER not in mechanisms


def test_generation_6_talks_to_bank_itself_and_is_handed_back_less_than_it_gives() -> None:
    # The line between the cartridge era and what came after. Black reaches Bank through Poke
    # Transporter, one way and permanently; X deposits and withdraws, so a living dex can be
    # kept in Bank rather than only sent there.
    for module in (x, y):
        [deposit] = [edge for edge in module.edges() if edge.to == bank.NODE]
        [withdrawal] = [edge for edge in module.edges() if edge.from_ == bank.NODE]

        # Two one-way edges rather than one both-ways edge, which is the whole point: the two
        # directions do not agree, and a both-ways edge can only say one thing about both.
        assert deposit.mechanism is TransferMechanism.BANK
        assert deposit.direction is TransferDirection.ONE_WAY
        assert isinstance(deposit.filter, AllSpeciesFilter)
        assert deposit.history is None

        assert withdrawal.direction is TransferDirection.ONE_WAY
        assert (withdrawal.history.from_, withdrawal.history.to) == (3, 6)

    assert bank.transporter_edge("black").direction is TransferDirection.ONE_WAY


def test_the_registry_can_tell_a_node_from_a_game_before_either_is_built() -> None:
    # The shared steps run before any game does and ask a source about every id the registry
    # holds. PokeAPI has a version group for Omega Ruby and has never heard of Pokemon Bank, so
    # the forms table has to be handed the games and not the nodes - and the first full build
    # after Bank was registered failed exactly there.
    registry = default_registry()

    assert bank.NODE in registry.game_ids
    assert home.NODE in registry.game_ids
    assert bank.NODE not in registry.playable_ids
    assert home.NODE not in registry.playable_ids
    assert len(registry.playable_ids) == len(registry.game_ids) - 2


def test_bank_is_a_node_rather_than_a_game() -> None:
    # The first entry in this registry that nobody plays. It is here because a route has to
    # point at something the validator counts as known, and everything that makes a game a game
    # is absent: no dex to fill, no region, no National Dex, nothing ever caught in it.
    data = bank.build(context(bank.NODE))

    assert data.game.release is GameRelease.SERVICE
    assert data.game.national_dex_through is None
    assert data.game.region == ""
    assert data.dex_entries == []
    assert data.acquisition_methods == []


def test_the_way_out_of_bank_is_declared_by_bank_and_waits_for_home() -> None:
    # The same thing every game does about a route whose other end is not written yet, and the
    # last one in the dataset: HOME is the only node left.
    [out] = bank.edges()

    assert (out.from_, out.to) == (bank.NODE, "home")
    assert out.mechanism is TransferMechanism.HOME
    assert out.direction is TransferDirection.ONE_WAY


def test_bank_will_not_hand_a_virtual_console_pokemon_to_generation_6() -> None:
    # The restriction that made a window necessary at all. Bank takes a Pokemon out of a
    # Virtual Console Red as readily as out of Black, and the two do not come back out the same
    # way: Generation 6 reads one and not the other. Nothing on the record says which it is, so
    # the edge has to.
    [withdrawal] = [edge for edge in x.edges() if edge.from_ == bank.NODE]

    assert withdrawal.history == bank.GENERATION_6_WITHDRAWAL
    assert (withdrawal.history.from_, withdrawal.history.to) == (3, 6)

    # A Generation 3 Pokemon really can be in Bank, having come the long way round, and X takes
    # it - so the floor is 3 rather than 5, which is where Transporter's own reach would put it.
    assert withdrawal.history.from_ == 3


def test_home_is_the_node_the_graph_ends_at() -> None:
    # The second and last of them, and the one that closes the dataset's graph: HOME declares no
    # route of its own, because nothing leaves it that is not a game's own business.
    data = home.build(context(home.NODE))

    assert data.game.release is GameRelease.SERVICE
    assert data.game.national_dex_through is None
    assert data.dex_entries == []
    assert data.acquisition_methods == []


def test_home_deposits_and_withdrawals_are_two_edges_because_one_would_refuse_everything() -> None:
    # Not a tidiness argument like Bank's. A both-ways edge carries one filter in both
    # directions, and this filter asks whether the game being transferred *into* lists the
    # species - so read backwards it asks HOME, whose dex is empty, and every deposit ever made
    # would have been refused.
    deposit, withdrawal = home.home_edges("sword")

    assert (deposit.from_, deposit.to) == ("sword", home.NODE)
    assert isinstance(deposit.filter, AllSpeciesFilter)
    assert deposit.direction is TransferDirection.ONE_WAY

    assert (withdrawal.from_, withdrawal.to) == (home.NODE, "sword")
    assert isinstance(withdrawal.filter, PresentInTargetDexFilter)
    assert withdrawal.direction is TransferDirection.ONE_WAY

    # Neither of them reads where a Pokemon has been. HOME's refusals are about lists, and the
    # one route into it that cannot be undone is one way rather than filtered.
    assert deposit.history is None
    assert withdrawal.history is None


def test_the_way_out_of_bank_is_lit_now_that_its_other_end_exists() -> None:
    # The last held-back edge in the dataset, declared by Bank at its own step and waiting since.
    # Nothing in bank.py was touched to light it.
    [out] = bank.edges()

    assert (out.from_, out.to) == (bank.NODE, home.NODE)
    assert out.direction is TransferDirection.ONE_WAY

    # One way, and the reason the 3DS era ends here: a Pokemon that has gone into HOME has no
    # route back to anything with a cartridge slot. The two routes that do leave HOME go to the
    # Let's Go pair and hand back only what those two produced themselves, so they take nothing
    # away from the sentence above: anything that reached HOME through Bank was converted to
    # Sword and Shield's format on the way in and can never enter them.
    leaving_home = [
        edge for edge in default_registry().edges if edge.from_ == home.NODE
    ]

    assert [edge.to for edge in leaving_home] == ["lets-go-eevee", "lets-go-pikachu"]
    assert all(edge.origin.games == list(lets_go.PAIR) for edge in leaving_home)


# --- Let's Go, Pikachu! and Let's Go, Eevee! --------------------------------------------------


def lets_go_entity(module):
    # No api worth the name: at step 1 a build of these two asks the source nothing at all.
    return module.build(context(module.GAME_ID)).game


def test_the_lets_go_pair_is_generation_7_in_kanto_on_a_home_console() -> None:
    pikachu = lets_go_entity(lets_go_pikachu)
    eevee = lets_go_entity(lets_go_eevee)

    # Generation 7 on the console Generation 8 belongs to. What decides it is the species the
    # game knows, and these know Kanto's 151 with one Mythical Pokemon added.
    assert (pikachu.generation, eevee.generation) == (7, 7)
    assert (pikachu.region, eevee.region) == (kanto.REGION, kanto.REGION)

    # One day, everywhere, which only Ultra Sun and Ultra Moon had managed before them.
    assert pikachu.released == date(2018, 11, 16)
    assert eevee.released == pikachu.released

    # No National Pokedex, like the four Alola cartridges before them - and unlike those four,
    # no boxes that hold what the list does not. Step 2 fills the list in.
    assert (pikachu.national_dex_through, eevee.national_dex_through) == (None, None)
    assert pikachu.dex_source is DexSource.GAME_DEX

    assert pikachu.pair_partner == eevee.id
    assert eevee.pair_partner == pikachu.id


def test_both_halves_show_the_same_list_and_it_is_not_kanto_s() -> None:
    api = FakeApi([(1, "bulbasaur"), (151, "mew"), (152, "meltan"), (153, "melmetal")])

    for module in (lets_go_pikachu, lets_go_eevee):
        data = module.build(context(module.GAME_ID, api))

        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "bulbasaur"),
            (151, "mew"),
            (152, "meltan"),
            (153, "melmetal"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)
        # One list, so a number can only belong to one: the dex name is X and Y's alone.
        assert all(entry.dex is None for entry in data.dex_entries)

    # Not "kanto", which is the 151 the other four games set here show. This one contains that
    # list exactly and puts two species at the end of it that Kanto never had.
    assert api.asked_for == [lets_go.DEX] * 2
    assert lets_go.DEX == "letsgo-kanto"
    assert lets_go.DEX != kanto.DEX


def test_the_lets_go_pair_reaches_its_other_half_and_home_and_nothing_else() -> None:
    edges = lets_go_pikachu.edges()

    # The first core games since Ruby and Sapphire that no other core game can reach. There is
    # no route to Ultra Sun, which came out a year earlier, and none to Bank at all.
    assert [(edge.from_, edge.to) for edge in edges] == [
        ("lets-go-pikachu", "lets-go-eevee"),
        ("lets-go-pikachu", "home"),
        ("home", "lets-go-pikachu"),
    ]

    [trade] = [edge for edge in edges if edge.to == "lets-go-eevee"]
    assert trade.direction is TransferDirection.BOTH_WAYS
    assert trade.mechanism is TransferMechanism.TRADE


def test_home_hands_these_two_back_only_what_started_in_them() -> None:
    edges = lets_go_eevee.edges()
    [deposit] = [edge for edge in edges if edge.to == home.NODE]
    [withdrawal] = [edge for edge in edges if edge.from_ == home.NODE]

    # The deposit is the ordinary one: HOME holds everything, so it takes everything.
    assert deposit.filter.filter == "all"
    assert deposit.origin is None

    # The withdrawal is the reason OriginRequirement exists, and the pair counts as one origin:
    # a Pokemon caught in Let's Go, Pikachu! may be withdrawn into Let's Go, Eevee!.
    assert withdrawal.filter.filter == "all"
    assert withdrawal.origin.games == ["lets-go-pikachu", "lets-go-eevee"]

    # Not home.home_edges, which is what the Generation 8 and 9 games get: that withdrawal asks
    # whether the target's dex lists the species, and every species this one refuses is listed.
    [_, generation_8] = home.home_edges("sword")
    assert generation_8.filter.filter == "presentInTargetDex"
    assert generation_8.origin is None


def kalos_slot(
    version: str,
    method: str,
    *,
    chance: int = 20,
    conditions: list[str] | None = None,
    area: str = "kalos-route-18-area",
) -> dict:
    return {
        "location_area": {"name": area},
        "version_details": [
            {
                "version": {"name": version},
                "encounter_details": [
                    {
                        "min_level": 44,
                        "max_level": 46,
                        "chance": chance,
                        "method": {"name": method},
                        "condition_values": [{"name": one} for one in (conditions or [])],
                    }
                ],
            }
        ],
    }


def kalos_wild(module, api: FakeApi) -> list:
    return [
        one
        for one in module.build(context(module.GAME_ID, api)).acquisition_methods
        if one.kind == "wild"
    ]


def test_each_kalos_half_reads_its_own_version_of_the_encounter_table() -> None:
    for module, rate in ((x, 20), (y, 45)):
        api = FakeApi(
            [(1, "sandslash")],
            {
                "sandslash": [
                    kalos_slot("x", "walk", chance=20),
                    kalos_slot("y", "walk", chance=45),
                ]
            },
        )

        wild = kalos_wild(module, api)

        # Three dexes, one encounter table read three times over - so the same slot arrives
        # once per list and all three say the same thing about it.
        assert {one.rate_percent for one in wild} == {rate}
        assert all(one.game == module.GAME_ID for one in wild)


def test_the_friend_safari_says_what_it_takes_before_it_says_where() -> None:
    # PokeAPI files it as eighteen ordinary areas full of ordinary tables. It is a room in a
    # city that opens after the Hall of Fame, holding whatever a stranger's friend code decided,
    # and the percentage beside each row is not an encounter rate at all.
    api = FakeApi(
        [(1, "ivysaur")],
        {"ivysaur": [kalos_slot("x", "walk", conditions=["friend-safari-slot-1"],
                                area="friend-safari-grass")]},
    )

    [found, *_] = kalos_wild(x, api)

    assert found.requirement == kalos.PLACE_GATES["Friend Safari"]
    assert "friend code" in found.requirement
    assert "not how often it turns up" in found.requirement


def test_the_third_friend_safari_slot_says_what_closed_in_2024() -> None:
    # The one thing in this dataset that got harder after the games came out: the third slot
    # opened when the friend appeared in the Player Search System, and that network is off.
    api = FakeApi(
        [(1, "ivysaur")],
        {"ivysaur": [kalos_slot("x", "walk", conditions=["friend-safari-slot-3"],
                                area="friend-safari-grass")]},
    )

    [found, *_] = kalos_wild(x, api)

    assert found.requirement.startswith(kalos.PLACE_GATES["Friend Safari"])
    assert "April 2024" in found.requirement


def test_kalos_gives_zygardes_chamber_back_its_apostrophe() -> None:
    # A sub-area has no name of its own in PokeAPI and is generated from the slug, which cannot
    # hold an apostrophe. Terminus Cave's bottom room is Zygarde's Chamber.
    assert kalos.RENAMED_SUB_AREAS["Zygardes Chamber"] == "Zygarde's Chamber"


def kalos_gifts(module, api: FakeApi) -> list:
    return [
        one
        for one in module.build(context(module.GAME_ID, api)).acquisition_methods
        if one.kind == "gift"
    ]


def test_kalos_hands_over_six_starters_which_no_game_had_done_since_firered() -> None:
    # Three at the table in Aquacorde Town and three more in Professor Sycamore's lab. Both sets
    # are starters rather than one set and a present: a player picks one of three either time.
    api = FakeApi(
        [(1, "chespin"), (2, "bulbasaur")],
        {
            "chespin": [kalos_slot("x", "gift")],
            "bulbasaur": [kalos_slot("x", "gift")],
        },
    )

    gifts = {one.target.species: one for one in kalos_gifts(x, api)}

    assert gifts["chespin"].gift_kind is GiftKind.STARTER
    assert gifts["bulbasaur"].gift_kind is GiftKind.STARTER
    assert gifts["chespin"].npc is None
    assert gifts["bulbasaur"].npc == "Professor Sycamore"


def test_a_fossil_says_which_of_the_two_it_was_and_what_the_other_one_is() -> None:
    # One of the pair is dug up and the other stays in the cave, so the answer to "how do I get
    # a Tyrunt" has to name the fossil and admit what picking it costs.
    api = FakeApi([(1, "tyrunt")], {"tyrunt": [kalos_slot("x", "gift")]})

    [found] = kalos_gifts(x, api)

    assert found.gift_kind is GiftKind.FOSSIL
    assert "Jaw Fossil" in found.requirement
    assert "Amaura" in found.requirement


def test_the_bird_a_save_gets_is_decided_by_the_starter_it_began_with() -> None:
    # The sharpest fact in this step, and it is in the encounter's own conditions rather than in
    # anything written here: one playthrough can reach one of the three, and the other two are a
    # trade. Which is which was checked against the wiki - Chespin brings Articuno.
    api = FakeApi(
        [(1, "articuno")],
        {"articuno": [kalos_slot("x", "static", conditions=["starter-chespin"])]},
    )

    [found] = kalos_gifts(x, api)

    assert found.gift_kind is GiftKind.STATIC_ENCOUNTER
    assert found.requirement == "Only in a save that started with Chespin"


def test_a_roaming_bird_stops_running_after_the_eleventh_meeting() -> None:
    api = FakeApi(
        [(1, "articuno")],
        {
            "articuno": [
                kalos_slot(
                    "x",
                    "static",
                    conditions=["starter-chespin", "other-found-11-times-roaming"],
                )
            ]
        },
    )

    [found] = kalos_gifts(x, api)

    assert "eleven times while roaming" in found.requirement


def test_a_gift_nobody_has_read_up_on_still_says_where_and_at_what_level() -> None:
    # Lapras is handed over on Route 12 and this dataset knows nothing else about it. The record
    # keeps what PokeAPI does know; inventing an NPC to fill the line would be worse than blank.
    api = FakeApi([(1, "lapras")], {"lapras": [kalos_slot("x", "gift")]})

    [found] = kalos_gifts(x, api)

    assert found.npc is None
    assert found.requirement is None
    assert found.level == 44
    assert "lapras" not in kalos.XY_GIFTS


def test_the_cover_legendary_is_the_one_static_the_two_halves_disagree_about() -> None:
    # Xerneas is on X's box and in X's Team Flare HQ; Yveltal is on Y's and in Y's. PokeAPI
    # files each under its own version, so this needs nothing written down - but it is the
    # version exclusive a player can see from the outside, so it is worth pinning.
    api = FakeApi(
        [(1, "xerneas"), (2, "yveltal")],
        {
            "xerneas": [kalos_slot("x", "static")],
            "yveltal": [kalos_slot("y", "static")],
        },
    )

    assert [one.target.species for one in kalos_gifts(x, api)] == ["xerneas"]
    assert [one.target.species for one in kalos_gifts(y, api)] == ["yveltal"]


def test_two_of_the_kalos_traders_will_take_whatever_is_in_the_party() -> None:
    # New in this pair: an in-game trade had always been one named species for another. Both of
    # these hand over a held item worth more than the Pokemon.
    anything = [one for one in kalos.XY_TRADES if one.wants is None]

    assert {one.gets for one in anything} == {"ralts", "eevee"}
    assert "Gardevoirite" in next(one for one in anything if one.gets == "ralts").requirement


def test_shaunas_trade_is_three_trades_one_per_save() -> None:
    # She takes the first partner yours is strong against and hands it back at the end, so a
    # save reaches two of the three and the third is in neither game at all.
    hers = [one for one in kalos.xy_trades() if one.npc == "Shauna"]

    assert {one.gets for one in hers} == {"chespin", "fennekin", "froakie"}
    assert kalos.SHAUNA_TRADE["chespin"] == "froakie"
    assert "started with Chespin" in next(one for one in hers if one.gets == "froakie").requirement


def test_the_aerodactyl_pokeapi_has_no_row_for_is_written_down_by_hand() -> None:
    # Coastal Kalos #068 with nothing in either encounter table, which read as an entry neither
    # half can fill. The Fossil Lab revives an Old Amber, and the Old Amber is under a rock.
    [amber] = kalos.XY_HANDED_OVER

    assert amber.species == "aerodactyl"
    assert amber.kind is GiftKind.FOSSIL
    assert "Rock Smash" in amber.requirement


def test_the_two_halves_keep_the_same_number_of_exclusives_as_each_other() -> None:
    # Sixteen each, which is what a version pair has always looked like. It came out three
    # against ten while the Friend Safari counted as a way to get one: a Safari holds what a
    # stranger's friend code decided and pays no attention to which cartridge is asking, so it
    # dissolved one half's exclusives and not the other's. Not counting it put the pair back
    # into balance without anybody deciding what the answer should be.
    assert len(x.ELSEWHERE_IN_GENERATION_6) == 16
    assert len(y.ELSEWHERE_IN_GENERATION_6) == 16
    assert set(x.ELSEWHERE_IN_GENERATION_6) & set(y.ELSEWHERE_IN_GENERATION_6) == set()

    # The cover legendaries are the pair a player can see from the outside.
    assert "yveltal" in x.ELSEWHERE_IN_GENERATION_6
    assert "xerneas" in y.ELSEWHERE_IN_GENERATION_6


def test_an_exclusive_a_safari_can_hold_says_so_and_still_reads_as_a_trade() -> None:
    # Both halves of the truth in one sentence: the way to fill this entry is a trade, and a
    # Safari might hold one if the right person is on the 3DS.
    assert x.ELSEWHERE_IN_GENERATION_6["spritzee"] == x.IN_A_SAFARI
    assert x.UNOBTAINABLE["spritzee"].startswith("Y only in Generation 6; trade one in.")
    assert "friend code" in x.UNOBTAINABLE["spritzee"]
    # And one no Safari holds says only the first half.
    assert x.UNOBTAINABLE["skrelp"] == "Y only in Generation 6; trade one in"


def test_the_friend_safari_is_recorded_and_not_counted() -> None:
    # The first place in the dataset that is both. The rows are true and a player cannot be
    # told to go and use them, so they are kept and left out of every count.
    api = FakeApi(
        [(1, "ivysaur")],
        {"ivysaur": [kalos_slot("x", "walk", area="friend-safari-grass")]},
    )

    [found] = kalos_wild(x, api)

    assert found.does_not_count == kalos.FRIEND_SAFARI_DOES_NOT_COUNT
    assert "friend code" in found.does_not_count


def test_an_ordinary_kalos_slot_still_counts() -> None:
    api = FakeApi([(1, "sandslash")], {"sandslash": [kalos_slot("x", "walk")]})

    [found] = kalos_wild(x, api)

    assert found.does_not_count is None


def test_a_kalos_exclusive_reads_as_generation_6_rather_than_as_an_older_number() -> None:
    assert x.UNOBTAINABLE["skrelp"] == "Y only in Generation 6; trade one in"
    assert y.UNOBTAINABLE["aron"].startswith("X only in Generation 6")


def test_both_halves_of_the_kalos_pair_are_drawn_from_one_sheet() -> None:
    # One sheet for the two of them, fetched once. It is not a sheet of drawings at all: X and Y
    # are in 3D, and what stands in for one is a shot of each model.
    for module in (x, y):
        assert module.build(context(module.GAME_ID)).game.sprite_set == "generation-vi/x-y"

    # Named for the pair, because Omega Ruby and Alpha Sapphire have one of their own.
    assert kalos.XY_SPRITE_SET != unova.SPRITE_SET
    assert kalos.XY_SPRITE_SET.startswith("generation-vi/")


def test_the_three_mythicals_are_in_the_dex_and_only_ever_given_away() -> None:
    # Central Kalos #151 to #153, which the games hold and do not ask for - the only entries in
    # any dex here that a player is excused from. A living dex asks for them anyway.
    for module in (x, y):
        for species in ("diancie", "hoopa", "volcanion"):
            reason = module.UNOBTAINABLE[species]

            assert reason.startswith("Nothing in Kalos produces one")
            assert "handed one out" in reason


def test_the_2014_championship_gave_each_half_what_it_cannot_catch() -> None:
    # Step 7's find. Three exclusives handed to X players and three to Y players, on the same
    # two days, each chosen for the half that has no way to it.
    assert "Korean World Championship" in x.UNOBTAINABLE["heracross"]
    assert "Korean World Championship" in x.UNOBTAINABLE["manectric"]
    assert "Korean World Championship" in x.UNOBTAINABLE["tyranitar"]
    assert "Korean World Championship" in y.UNOBTAINABLE["aggron"]
    assert "Korean World Championship" in y.UNOBTAINABLE["houndoom"]
    assert "Korean World Championship" in y.UNOBTAINABLE["pinsir"]


def test_an_entry_with_both_a_safari_and_a_giveaway_says_both() -> None:
    # Three sentences, in the order a player would want them: trade for one, a Safari might
    # hold one, and here is what once handed one over.
    reason = x.UNOBTAINABLE["heracross"]

    assert reason.startswith("Y only in Generation 6; trade one in.")
    assert "A Friend Safari can hold one" in reason
    assert reason.endswith("handed one out")
    # Capitalised properly rather than flattened: the names of the distributions are names.
    assert "Summer 2014 Heracross" in reason


def test_an_entry_nothing_ever_handed_out_says_only_the_first_half() -> None:
    assert x.UNOBTAINABLE["skrelp"] == "Y only in Generation 6; trade one in"
    assert y.UNOBTAINABLE["aron"] == "X only in Generation 6; trade one in"


def kalos_form(form_id: str, species: str, kind: FormKind = FormKind.COSMETIC) -> Form:
    return Form(id=form_id, species=species, name=form_id, kind=kind, games=["x", "y"])


def test_one_sentence_answers_for_every_vivillon_pattern() -> None:
    # Nineteen patterns and one answer, keyed by species rather than listed: the answer is the
    # same for each, and a list of nineteen ids is a list to get wrong.
    patterns = [kalos_form(f"vivillon-{name}", "vivillon") for name in ("sun", "polar", "fancy")]

    changes = kalos.xy_form_changes(patterns)

    assert {change.requirement for change in changes.values()} == {
        kalos.XY_FORM_CHANGES_BY_SPECIES["vivillon"].requirement
    }
    # The fact that makes this pair's forms unlike any before them: the console decides.
    assert "country and region" in changes["vivillon-sun"].requirement


def test_a_furfrou_trim_says_it_cannot_be_kept() -> None:
    # The one form in the dataset a living dex cannot hold: five days, and gone the moment it
    # goes in a box. Saying where to get it and not that would be half an answer.
    [trim] = kalos.xy_form_changes([kalos_form("furfrou-kabuki", "furfrou")]).values()

    assert "five days" in trim.requirement
    assert "put in a box" in trim.requirement
    assert trim.where == "Lumiose City"


def test_each_item_that_changes_an_older_legendary_is_a_favour_for_showing_it() -> None:
    # All four are in Kalos and all four are handed over for showing the legendary itself -
    # which no Kalos save can catch. The Pokemon has to come first, and the item follows.
    changes = kalos.XY_FORM_CHANGES

    assert "Reveal Glass" in changes["landorus-therian"].requirement
    assert changes["landorus-therian"].where == "Reflection Cave"
    assert "DNA Splicers" in changes["kyurem-black"].requirement
    assert "Griseous Orb" in changes["giratina-origin"].requirement
    assert "Gracidea" in changes["shaymin-sky"].requirement
    assert all("shown" in changes[form].requirement for form in ("kyurem-black", "shaymin-sky"))


def test_a_form_with_no_way_here_gets_no_record_rather_than_a_guess() -> None:
    # AZ's Floette was never handed over by any game, and its four colour siblings are caught in
    # the grass - so the species-wide answer must not quietly cover it.
    forms = [
        kalos_form("floette-blue", "floette"),
        kalos_form("floette-eternal", "floette", FormKind.FUNCTIONAL),
    ]

    changes = kalos.xy_form_changes(forms)

    assert "floette-blue" in changes
    assert "floette-eternal" not in changes
    assert "floette-eternal" in kalos.XY_NO_WAY_HERE


def test_the_seasons_are_gone_and_kalos_says_so() -> None:
    [coat] = kalos.xy_form_changes([kalos_form("deerling-winter", "deerling")]).values()

    assert "no seasons" in coat.requirement
    assert "hatch" in coat.requirement


def test_a_sex_needs_no_table_here_either() -> None:
    # Ninety-nine of this pair's forms are a sex, and not one of them is written down: the
    # answer is the same everywhere and `formchanges` keeps it.
    assert "pikachu-female" not in kalos.xy_form_changes([kalos_form("pikachu-female", "pikachu")])


# --- Omega Ruby and Alpha Sapphire ------------------------------------------------------------


def oras_slot(
    version: str,
    method: str,
    *,
    area: str = "hoenn-route-101-area",
    conditions: list[str] | None = None,
) -> dict:
    return {
        "location_area": {"name": area},
        "version_details": [
            {
                "version": {"name": version},
                "encounter_details": [
                    {
                        "min_level": 20,
                        "max_level": 22,
                        "chance": 30,
                        "method": {"name": method},
                        "condition_values": [{"name": one} for one in (conditions or [])],
                    }
                ],
            }
        ],
    }


def test_the_hoenn_remakes_are_two_games_that_name_each_other() -> None:
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID)).game
        for module in (omega_ruby, alpha_sapphire)
    }

    assert sorted(both) == ["alpha-sapphire", "omega-ruby"]
    assert both["omega-ruby"].pair_partner == "alpha-sapphire"
    assert both["alpha-sapphire"].pair_partner == "omega-ruby"
    assert both["omega-ruby"].title != both["alpha-sapphire"].title
    # One day in Japan, America, Australia, Korea, Hong Kong and Taiwan, and a week later in
    # Europe - so not quite the single worldwide day X and Y had a year before.
    assert both["omega-ruby"].released == both["alpha-sapphire"].released == date(2014, 11, 21)


def test_the_hoenn_remakes_are_generation_6_cartridges_set_in_generation_3s_region() -> None:
    # The whole reason the region and the generation are two modules: these two say Hoenn, like
    # three cartridges written twelve years earlier, and every other fact about them belongs to
    # the generation that X and Y opened.
    for module in (omega_ruby, alpha_sapphire):
        game = module.build(context(module.GAME_ID)).game

        assert game.generation == 6
        assert game.region == "Hoenn"
        assert game.national_dex_through == 721
        assert game.dex_source is DexSource.NATIONAL_DEX
        assert game.release is GameRelease.CARTRIDGE

    assert ruby.build(context("ruby")).game.region == "Hoenn"
    assert ruby.build(context("ruby")).game.generation == 3


def test_hoenn_outlives_its_generation_and_the_modules_are_split_for_it() -> None:
    # Hoenn joins Kanto, Johto and Kalos as a region whose games are not all from one
    # generation, and it took the second one the way Kanto did when FireRed arrived: every
    # Generation 3 fact in the region module now says which generation it is a fact about, so
    # nothing can hand a remake a link cable or a 202-entry Pokedex by having the shorter name.
    assert hoenn.REGION == "Hoenn"
    assert not hasattr(hoenn, "GENERATION")
    assert not hasattr(hoenn, "cartridge")
    assert not hasattr(hoenn, "dex_entries")
    assert hoenn.GBA_DEX == "hoenn"
    assert hoenn.GBA_NATIONAL_DEX_THROUGH == 386
    # And what stayed unprefixed is the one thing both generations really do share.
    assert hoenn.DAY_CARE == "Route 117, Pokemon Day Care"


def test_the_remakes_show_a_different_pokedex_from_the_region_they_remake() -> None:
    # Two games set in the same region, both calling the list "the Hoenn Pokedex", and they are
    # not the same list: 211 entries against 202. Which one a game asks PokeAPI for is the whole
    # of step 2, and getting it wrong would renumber a game by hand.
    api = FakeApi([(1, "treecko")])

    omega_ruby.build(context("omega-ruby", api))
    ruby.build(context("ruby", api))

    assert api.asked_for == ["updated-hoenn", "hoenn"]
    assert hoenn.ORAS_DEX_TOTAL == 211


def test_both_remakes_show_the_same_list_and_number_it_the_same_way() -> None:
    api = FakeApi([(1, "treecko"), (2, "grovyle")])
    both = {
        module.GAME_ID: module.build(context(module.GAME_ID, api)).dex_entries
        for module in (omega_ruby, alpha_sapphire)
    }

    assert [one.number for one in both["omega-ruby"]] == [1, 2]
    assert [(one.target.species, one.number) for one in both["omega-ruby"]] == [
        (one.target.species, one.number) for one in both["alpha-sapphire"]
    ]
    assert all(one.game == "omega-ruby" for one in both["omega-ruby"])


def test_the_remakes_show_one_pokedex_and_so_do_not_name_it() -> None:
    # X and Y had to say which of three lists an entry was numbered in. These two show one, like
    # the twenty games before them, and a number that can only belong to one list says nothing.
    entries = omega_ruby.build(context("omega-ruby")).dex_entries

    assert entries
    assert all(one.dex is None for one in entries)


def test_the_remakes_read_their_wild_off_the_wiki_rather_than_the_api() -> None:
    # The one game in this dataset whose encounter tables are not PokeAPI's. It has rows for
    # these two versions - hordes, the Mirage spots - and no grass, no water and no fishing at
    # all, so what a player would call the game is missing from the source.
    api = FakeApi([(1, "treecko")], {"treecko": [oras_slot("omega-ruby", "walk")]})
    wiki = FakeWiki("Treecko")

    [found] = [
        one
        for one in omega_ruby.build(context("omega-ruby", api, wiki=wiki)).acquisition_methods
        if one.kind == "wild"
    ]

    assert found.source.source == "bulbapedia"
    assert found.method is EncounterMethod.WALK
    assert (found.levels.minimum, found.levels.maximum) == (5, 7)
    # Sixty-nine pages, each fetched once, and the place named the way the rest of the dataset
    # names it rather than the way the wiki titles it.
    assert len(wiki.asked_for) == len(hoenn.ORAS_PAGES) == 69
    assert found.location == "Route 101"


def test_a_place_the_wiki_pages_do_not_cover_still_comes_from_the_api() -> None:
    # The Mirage spots are the other half of this pair's wild: islands, caves, forests and
    # mountains that appear off the coast for a day and hold what Hoenn otherwise does not.
    # PokeAPI has their tables and the wiki keeps them on pages that are not tables at all, so
    # each source answers where the other is silent.
    api = FakeApi(
        [(1, "treecko")],
        {"treecko": [oras_slot("omega-ruby", "walk", area="mirage-spot-cave-north-of-fallarbor")]},
    )

    wild = [
        one
        for one in omega_ruby.build(context("omega-ruby", api)).acquisition_methods
        if one.kind == "wild"
    ]

    [mirage] = [one for one in wild if one.source.source == "pokeapi"]
    assert mirage.location == "Mirage Cave"
    # And the joining word is not shouted, which is what a slug made into a name does.
    assert mirage.sub_area == "North of Fallarbor"


def test_a_place_both_sources_know_about_is_the_wikis() -> None:
    # Otherwise every horde in Hoenn would be recorded twice: PokeAPI has them for the routes,
    # and so does the page this step reads.
    api = FakeApi([(1, "treecko")], {"treecko": [oras_slot("omega-ruby", "horde")]})

    wild = [
        one
        for one in omega_ruby.build(context("omega-ruby", api)).acquisition_methods
        if one.kind == "wild"
    ]

    assert [one.source.source for one in wild] == ["bulbapedia"]


def test_which_half_has_a_species_is_a_colour_on_the_page() -> None:
    # The two cells say "OR" and "AS" whichever game a row belongs to. Reading the letters
    # would hand both halves every exclusive in Hoenn; the filled-in background is the answer.
    api = FakeApi([(1, "treecko")])
    wiki = FakeWiki("Treecko", in_alpha_sapphire=False)

    both = {
        module.GAME_ID: [
            one
            for one in module.build(context(module.GAME_ID, api, wiki=wiki)).acquisition_methods
            if one.kind == "wild"
        ]
        for module in (omega_ruby, alpha_sapphire)
    }

    assert len(both["omega-ruby"]) == 1
    assert both["alpha-sapphire"] == []


def test_the_two_ways_hoenn_was_never_reachable_before_are_methods_of_their_own() -> None:
    # Under the sea and over it. Both are this pair's own, both are a table rather than a rarer
    # kind of surfing, and both are what the games are remembered for.
    assert hoenn.ORAS_METHODS["Dive"] is EncounterMethod.DIVE
    assert hoenn.ORAS_METHODS["Seaweed"] is EncounterMethod.DIVE
    assert hoenn.ORAS_METHODS["Flocks"] is EncounterMethod.SOARING


def test_the_dexnav_gets_a_sentence_rather_than_the_wikis_four_words() -> None:
    # A hundred and sixty-five rows of these two games are "Exclusively as hidden Pokemon",
    # which says nothing to anybody who has not read the rest of the page. The wiki words it
    # four ways - the sea gets its own, and half the pages say "capturing" where the rest say
    # "catching" - and all four mean the same sentence here.
    hidden = [
        one
        for key, one in hoenn.ORAS_CONDITIONS.items()
        if "hidden Pokémon After" in key or "hidden Pokémon )" in key
    ]

    assert len(hidden) == 4
    assert len(set(hidden)) == 1
    assert "DexNav" in hidden[0]
    assert "Groudon or Kyogre" in hidden[0]
    # And a heading that says only what the record already carries is rewritten as nothing.
    assert hoenn.ORAS_CONDITIONS["Underwater"] == ""


def test_a_remake_cannot_trade_with_the_game_it_remakes() -> None:
    # The obvious route that does not exist. Ruby and Omega Ruby are the same region and the
    # same story, and no cable reaches a Game Boy Advance cartridge from a 3DS: what a Ruby has
    # to travel is Pal Park, the Poke Transfer, Poke Transporter and Bank.
    # Bank's withdrawal is declared here too and starts at Bank, so the far end of each route
    # is what is asked for rather than the `to` of each edge.
    reached = {edge.to if edge.from_ == omega_ruby.GAME_ID else edge.from_ for edge in
               omega_ruby.edges()}

    assert reached == {"x", "y", "alpha-sapphire", "bank"}
    assert "ruby" not in reached
    assert "ruby" not in {edge.to for edge in alpha_sapphire.edges()}
    assert "omega-ruby" not in {edge.to for edge in ruby.edges()}


def test_both_remakes_show_the_same_cover_the_picker_will_draw() -> None:
    # Registered at step 1 like every game before them, so the picker has a cover to draw from
    # the first build that knows these two exist.
    registry = default_registry()

    assert registry.box_art_of("omega-ruby") == "Omega Ruby EN boxart.png"
    assert registry.box_art_of("alpha-sapphire") == "Alpha Sapphire EN boxart.png"


def test_the_remakes_hand_over_twelve_first_partners_which_no_game_had_done() -> None:
    # Three on Route 101 the way Hoenn always has, and then Johto's, Unova's and Sinnoh's, each
    # after something a player has finished. Four choices of three, so a save keeps four of the
    # twelve and the other eight are a trade away.
    starters = {
        species: one
        for species, one in hoenn.ORAS_GIFTS.items()
        if isinstance(one, GiftDetail) and one.kind is GiftKind.STARTER
    }

    assert len(starters) == 12
    assert all(one.npc == "Professor Birch" for one in starters.values())
    assert {"treecko", "chikorita", "snivy", "turtwig"} <= set(starters)
    assert "Delta Episode" in starters["snivy"].requirement
    assert "second time" in starters["turtwig"].requirement


def test_a_mirage_spot_asks_for_a_party_before_it_appears_at_all() -> None:
    # What makes these two games a living dex in a way no game before them was: the legendaries
    # of five generations, each standing on an island that only rises for a player who has
    # already built something. PokeAPI cannot know that, so the place says it.
    api = FakeApi(
        [(1, "raikou")],
        {"raikou": [oras_slot("omega-ruby", "static", conditions=["time-minute-00-to-19"])]},
    )

    [found] = [
        one
        for one in hoenn.gen6_acquisition_methods(
            context("omega-ruby", api),
            game_id="omega-ruby",
            version="omega-ruby",
            column="OR",
            entries=[],
        )
        if one.kind == "gift"
    ]

    # The place's own sentence comes first and the row's own condition after it. Neither would
    # do on its own: the forest is not there without the bird, and which of the three beasts is
    # standing in it is the minute of the hour.
    assert found.requirement == (
        "The Trackless Forest appears east of Petalburg Woods only with Ho-Oh or Lugia in the "
        "party and in the first twenty minutes of the hour"
    )
    assert "maxed EVs" in hoenn.PATHLESS_PLAIN
    assert hoenn.ORAS_GIFTS["cobalion"].gate == hoenn.PATHLESS_PLAIN
    # PokeAPI has two of Cobalion's three days and files the third with no condition at all, so
    # the days are written out and its three rows collapse into one record.
    assert hoenn.ORAS_GIFTS["cobalion"].requirement == "On a Wednesday, a Friday or a Sunday"


def test_the_fossils_are_written_by_hand_because_no_table_has_them() -> None:
    # Nine species that are an item carried to the Devon Corporation rather than a Pokemon met
    # anywhere, and PokeAPI has an encounter for none of them.
    both = {one.species for one in hoenn.ORAS_FOSSILS_BOTH}
    omega = {one.species for one in hoenn.ORAS_HANDED_OVER["omega-ruby"]}
    alpha = {one.species for one in hoenn.ORAS_HANDED_OVER["alpha-sapphire"]}

    assert both == {"lileep", "anorith", "aerodactyl"}
    assert omega == {"kabuto", "shieldon", "archen"}
    assert alpha == {"omanyte", "cranidos", "tirtouga"}
    assert not omega & alpha
    assert all(one.kind is GiftKind.FOSSIL for one in hoenn.oras_handed_over("omega-ruby"))
    # The choice Hoenn has always asked for, and the answer that has never changed.
    [root] = [one for one in hoenn.ORAS_FOSSILS_BOTH if one.species == "lileep"]
    assert "lost for good" in root.requirement


def test_the_eon_duo_swap_places_between_the_halves() -> None:
    # Each half meets one of them in its own story and the other waits on the same island for
    # anybody holding a ticket that was only ever handed out at an event.
    omega = hoenn.oras_gifts("omega-ruby")
    alpha = hoenn.oras_gifts("alpha-sapphire")

    assert "in the story" in omega["latios"].requirement
    assert "Eon Ticket" in omega["latias"].requirement
    assert "in the story" in alpha["latias"].requirement
    assert "Eon Ticket" in alpha["latios"].requirement
    # Written as statics, which is also what folds PokeAPI's two rows for one island into one.
    assert all(
        omega[species].kind is GiftKind.STATIC_ENCOUNTER for species in ("latias", "latios")
    )


def test_the_remakes_trade_the_same_three_towns_and_not_the_same_trades() -> None:
    # Rustboro, Fortree and Pacifidlog, as in Ruby and Sapphire - and Fortree wants a Spinda
    # where it wanted a Pikachu, which is a Hoenn Pokemon put where a Kanto one had been. The
    # two trainers whose names the game records swapped towns as well.
    remade = {one.location: one for one in hoenn.ORAS_TRADES}
    older = {one.location: one for one in hoenn.GBA_PAIR_TRADES}

    assert sorted(remade) == sorted(older)
    assert remade["Fortree City"].wants == "spinda"
    assert older["Fortree City"].wants == "pikachu"
    assert remade["Rustboro City"].npc == "Darrell"
    assert older["Rustboro City"].npc == "Elyssa"
    assert remade["Fortree City"].npc == "Elyssa"


def test_the_remakes_evolve_by_their_own_version_group() -> None:
    api = FakeApi([(1, "treecko"), (2, "grovyle")])

    for module in (omega_ruby, alpha_sapphire):
        methods = module.build(context(module.GAME_ID, api)).acquisition_methods
        evolutions = [one for one in methods if one.kind == "evolution"]

        assert [one.target.species for one in evolutions] == ["grovyle"]

    # Their own group, and not the one the three cartridges in the same region share.
    assert hoenn.ORAS_VERSION_GROUP == "omega-ruby-alpha-sapphire"
    assert hoenn.GBA_PAIR_VERSION_GROUP == "ruby-sapphire"


def test_each_half_keeps_seven_and_a_whole_line_is_missing_rather_than_two_thirds() -> None:
    # Ruby and Sapphire split six entries; these two split seven, and the extra one is the same
    # line's last stage. The remakes' Pokedex holds every stage of the Lotad and Seedot lines
    # where Generation 3's stopped short, so a line that is not here is three entries.
    assert len(omega_ruby.ONLY_ON_ALPHA_SAPPHIRE) == len(alpha_sapphire.ONLY_ON_OMEGA_RUBY) == 7
    assert {"lotad", "lombre", "ludicolo"} <= set(omega_ruby.ONLY_ON_ALPHA_SAPPHIRE)
    assert {"seedot", "nuzleaf", "shiftry"} <= set(alpha_sapphire.ONLY_ON_OMEGA_RUBY)
    # Nothing is on both lists, which is what a version pair means.
    assert not set(omega_ruby.ONLY_ON_ALPHA_SAPPHIRE) & set(alpha_sapphire.ONLY_ON_OMEGA_RUBY)
    assert omega_ruby.UNOBTAINABLE["kyogre"].startswith(
        "Alpha Sapphire only in Generation 6; trade one in"
    )
    assert alpha_sapphire.UNOBTAINABLE["groudon"].startswith(
        "Omega Ruby only in Generation 6; trade one in"
    )


def test_the_third_stage_of_a_missing_line_is_explained_rather_than_evolved_into() -> None:
    # The quiet way this goes wrong: a game records "evolve a Lombre" for its Ludicolo, and
    # nothing in it can produce a Lotad. The evolution record is true and the entry is still
    # one this half cannot fill, so it says so.
    entries = {
        one.target.species: one
        for one in omega_ruby.build(context("omega-ruby", FakeApi([(1, "ludicolo")]))).dex_entries
    }

    assert entries["ludicolo"].unobtainable_reason == (
        "Alpha Sapphire only in Generation 6; trade one in"
    )


def test_step_7_read_every_entry_either_half_cannot_fill() -> None:
    # Fifteen entries and four hits. Both legendaries were given away by the same campaign, a
    # Mawile went out in South Korea and a Sableye in Japan, and the eleven others were never
    # handed out at all - which is an answer too, and the reason the tables carry None.
    events = {
        **omega_ruby.ONLY_ON_ALPHA_SAPPHIRE,
        **alpha_sapphire.ONLY_ON_OMEGA_RUBY,
    }

    assert sorted(species for species, event in events.items() if event) == [
        "groudon",
        "kyogre",
        "mawile",
        "sableye",
    ]
    assert "Dahara City" in events["kyogre"]
    assert "Dahara City" in events["groudon"]


def test_the_one_entry_no_game_has_ever_produced_says_so_in_both_halves() -> None:
    # Jirachi has never been catchable anywhere, in any generation. Generation 3's answer was a
    # bonus disc that came with another game; this one's is nine distributions, and the one most
    # players outside Japan could have had is the twentieth anniversary giveaway of April 2016.
    for module in (omega_ruby, alpha_sapphire):
        reason = module.UNOBTAINABLE["jirachi"]

        assert reason == hoenn.ORAS_JIRACHI_REASON
        assert "only been given away" in reason
        assert "20th Anniversary" in reason


def hoenn_form(form_id: str, species: str, kind: FormKind = FormKind.COSMETIC) -> Form:
    return Form(
        id=form_id, species=species, name=form_id, kind=kind, games=["omega-ruby", "alpha-sapphire"]
    )


def test_every_item_that_changes_a_form_is_somewhere_else_in_hoenn() -> None:
    # The same forms X and Y explain, and not one of the items is in the same place - which is
    # the whole reason a form's answer belongs to the region rather than to the generation.
    changes = hoenn.ORAS_FORM_CHANGES

    assert changes["landorus-therian"].where == "Mauville City"
    assert "selling mirrors" in changes["landorus-therian"].requirement
    assert "Gnarled Den" in changes["kyurem-black"].requirement
    assert "Route 130" in changes["giratina-origin"].requirement
    assert changes["shaymin-sky"].where == "Route 123"
    # Kalos sends a player somewhere else for every one of them.
    assert changes["landorus-therian"].where != kalos.XY_FORM_CHANGES["landorus-therian"].where


def test_the_form_these_two_invented_cannot_be_kept_either() -> None:
    # Hoopa Unbound is the second form in the dataset a living dex cannot hold, after Furfrou's
    # trim: three days, and back in the bottle the moment it is put in a box.
    unbound = hoenn.ORAS_FORM_CHANGES["hoopa-unbound"]

    assert "Prison Bottle" in unbound.requirement
    assert "three days" in unbound.requirement
    assert "box" in unbound.requirement


def test_deoxys_changes_forme_at_the_meteorite_these_games_have_a_fetch_quest_about() -> None:
    # What step 8 found in the shared table: the three formes were pinned to the Generation 3
    # cartridges that hold one each, and every game since Diamond has a meteorite that cycles
    # through all four.
    [forme] = set(
        hoenn.oras_form_changes(
            [hoenn_form("deoxys-attack", "deoxys", FormKind.FUNCTIONAL)], game_id="omega-ruby"
        ).values()
    )

    assert forme.where == "Fallarbor Town, Professor Cozmo's house"
    assert "cycles through all four" in forme.requirement


def test_the_east_sea_shellos_is_one_half_of_the_pairs_and_not_the_others() -> None:
    # The only form in this dataset whose answer is the version's. Both halves hold Shellos in
    # the same two places, and which sea it belongs to is what differs.
    forms = [hoenn_form("shellos-east", "shellos"), hoenn_form("gastrodon-east", "gastrodon")]

    alpha = hoenn.oras_form_changes(forms, game_id="alpha-sapphire")
    omega = hoenn.oras_form_changes(forms, game_id="omega-ruby")

    assert "East Sea kind" in alpha["shellos-east"].requirement
    assert "shellos-east" not in omega
    assert "gastrodon-east" not in omega


def test_the_cosplay_pikachu_is_six_costumes_that_cannot_leave_the_cartridge() -> None:
    # Nothing else in the dataset is like it: it cannot evolve, cannot breed, and cannot be
    # traded or put into Bank. A player who wants those six in a living dex has to keep the
    # cartridge they were given on.
    costumes = [
        hoenn_form(one, "pikachu")
        for one in ("pikachu-libre", "pikachu-belle", "pikachu-cosplay")
    ]

    changes = hoenn.oras_form_changes(costumes, game_id="omega-ruby")

    assert sorted(changes) == ["pikachu-belle", "pikachu-cosplay", "pikachu-libre"]
    [one] = set(changes.values())
    assert one.where == "Any Contest Hall"
    assert "cannot be traded or put into Bank" in one.requirement
    # Written out as six rather than keyed by species: a female Pikachu is a form too, and it
    # is not in a costume.
    assert "pikachu" not in hoenn.ORAS_FORM_CHANGES_BY_SPECIES
    assert hoenn.oras_form_changes(
        [hoenn_form("pikachu-female", "pikachu", FormKind.GENDER)], game_id="omega-ruby"
    ) == {}


def test_a_species_hoenn_does_not_have_gets_no_form_records_at_all() -> None:
    # Seventy-five forms over nine species, and every one for the same reason: Unown wants ruins
    # that are in Johto, and Vivillon, Furfrou, Flabebe and Pumpkaboo all want Kalos - the other
    # half of this generation and a different pair of games.
    forms = [
        hoenn_form("unown-b", "unown"),
        hoenn_form("vivillon-sun", "vivillon"),
        hoenn_form("furfrou-kabuki", "furfrou"),
        hoenn_form("rotom-heat", "rotom", FormKind.FUNCTIONAL),
    ]

    changes = hoenn.oras_form_changes(forms, game_id="omega-ruby")

    assert sorted(changes) == ["rotom-heat"]
    assert changes["rotom-heat"].where == "Littleroot Town, Professor Birch's lab"


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


# --- Generation 7: Alola ------------------------------------------------------------------


def test_the_alola_pair_says_what_it_is() -> None:
    # Step 1 and nothing more: a name, a partner, a day and a number.
    game = sun.build(context(sun.GAME_ID)).game

    assert (game.generation, game.region) == (7, "Alola")
    assert game.release is GameRelease.CARTRIDGE
    assert game.released == date(2016, 11, 18)
    assert game.pair_partner == "moon"
    assert moon.build(context(moon.GAME_ID)).game.pair_partner == "sun"

    # The decision this region forced. These are the first games since Generation 2 with no
    # National Pokedex - the Rotom Dex shows Alola's 302 and the National list moved to Bank -
    # and the number is filled in anyway, because what a living dex here asks for is everything
    # the boxes can hold rather than everything the dex app will name.
    assert game.national_dex_through == 802
    assert game.dex_source is DexSource.NATIONAL_DEX


def test_the_two_alola_dexes_are_two_lists_rather_than_one_longer_one() -> None:
    # The thing to know about this region. Platinum's Sinnoh dex was Diamond's with more after
    # it; the hundred and one Ultra Sun and Ultra Moon add are scattered through theirs, so the
    # numbering parts company at #024 and most of what follows disagrees.
    assert alola.SM_DEX != alola.USUM_DEX
    assert (alola.SM_DEX_TOTAL, alola.USUM_DEX_TOTAL) == (302, 403)
    assert alola.USUM_DEX_TOTAL - alola.SM_DEX_TOTAL == 101


def test_a_cable_between_the_two_alola_pairs_refuses_the_five_the_newer_one_added() -> None:
    # The Time Capsule's shape again, twenty years on: a both-ways route that carries everything
    # in one direction and stops short in the other. Poipole, Naganadel, Stakataka, Blacephalon
    # and Zeraora cannot be traded into Sun or Moon, which cannot read them.
    within = [edge for edge in sun.edges() if edge.to == "moon"]
    across = [edge for edge in sun.edges() if edge.to in alola.ULTRA]

    [inside] = within
    assert isinstance(inside.filter, AllSpeciesFilter)

    assert len(across) == 2
    for edge in across:
        assert edge.direction is TransferDirection.BOTH_WAYS
        assert (edge.filter.from_, edge.filter.to) == (1, 802)

    # Written once, in the region's own file, rather than at each end: a filter is not part of
    # what makes two declarations the same edge, so two games declaring this route differently
    # would collapse into whichever was seen first.
    assert isinstance(alola.carried_between("ultra-sun", "ultra-moon"), AllSpeciesFilter)


def test_bank_hands_alola_what_generation_6_could_not_have() -> None:
    # The payoff the Bank step predicted. Bank refuses a Generation 6 game anything that came
    # out of a Virtual Console Red or Gold; these it does not refuse, and that route is the whole
    # reason Generations 1 and 2 are in this dataset as their 3DS releases.
    [withdrawal] = [edge for edge in sun.edges() if edge.from_ == bank.NODE]
    [deposit] = [edge for edge in sun.edges() if edge.to == bank.NODE]

    assert withdrawal.history is None
    assert isinstance(deposit.filter, AllSpeciesFilter)

    # But the same five species are refused whatever route they came by, so the withdrawal is
    # capped where the cable is.
    assert (withdrawal.filter.from_, withdrawal.filter.to) == (1, 802)
    assert isinstance(alola.bank_carries("ultra-sun"), AllSpeciesFilter)


def test_no_cartridge_of_generation_6_trades_with_one_of_generation_7() -> None:
    # Both sit in the same 3DS and neither can see the other. What stands between them is Bank,
    # which is not a game, and the route is two steps rather than one cable.
    reached = {edge.to for edge in sun.edges()} | {edge.from_ for edge in sun.edges()}

    assert reached & {"x", "y", "omega-ruby", "alpha-sapphire"} == set()
    assert bank.NODE in reached


def test_both_halves_of_alola_show_the_same_302_entries_in_the_same_order() -> None:
    # One list for the pair, and one list per pair rather than per region: Ultra Sun and Ultra
    # Moon show a different one, which is why the constant is named for the pair.
    api = FakeApi([(1, "rowlet"), (302, "marshadow")])

    for module in (sun, moon):
        data = module.build(context(module.GAME_ID, api))

        assert [(entry.number, entry.target.species) for entry in data.dex_entries] == [
            (1, "rowlet"),
            (302, "marshadow"),
        ]
        assert all(entry.game == module.GAME_ID for entry in data.dex_entries)
        # One list, so no name on the entries. X and Y carry three and a player picks between
        # them; Alola's four islands are a way of reading one list rather than four lists.
        assert all(entry.dex is None for entry in data.dex_entries)

    assert api.asked_for == [alola.SM_DEX] * 2
    assert alola.SM_DEX == "original-alola"


def test_the_four_island_dexes_are_left_out_on_purpose() -> None:
    # The source has all four, numbered from 1. Those numbers are the guidebooks': in the game a
    # Pokemon keeps its overall Alola number wherever it is listed, so writing them would print
    # numbers no player was ever shown. They are named so the next person knows they were looked
    # at rather than missed.
    assert len(alola.ISLAND_DEXES) == 4
    assert alola.SM_DEX not in alola.ISLAND_DEXES

    api = FakeApi([(1, "rowlet")])
    sun.build(context(sun.GAME_ID, api))

    assert not set(api.asked_for) & set(alola.ISLAND_DEXES)


def test_the_alola_dex_is_not_the_living_dex_these_games_ask_for() -> None:
    # The decision this region forced, and the one place both halves of it are visible at once:
    # the list the game displays is 302 long and the grid is 802, because the boxes here hold
    # everything Bank will hand over and only the Pokedex stops early.
    data = sun.build(context(sun.GAME_ID, FakeApi([(1, "rowlet"), (302, "marshadow")])))

    assert len(data.dex_entries) == 2
    assert data.game.national_dex_through == 802


def test_a_place_is_turned_into_the_page_its_encounter_table_is_on() -> None:
    # A rule and two exceptions rather than a table of fifty-seven, because Alola's names carry
    # across almost unchanged. Six generations have had a Route 2, so a route is disambiguated by
    # its region; and the source writes some of the Hawaiian names with a curly apostrophe.
    assert alola.page_of("Route 2") == "Alola_Route_2"
    assert alola.page_of("Brooklet Hill") == "Brooklet_Hill"
    assert alola.page_of(f"Kala{chr(0x2019)}e Bay") == "Kala'e_Bay"

    # And the two the rule cannot reach: the wiki has no region in the Berry fields' title, and
    # every wild slot the source files under Royal Avenue is in the abandoned Thrifty Megamart,
    # which has a page of its own and stands on another island.
    assert alola.page_of("Alola Berry Fields") == "Berry_fields"
    assert alola.page_of("Royal Avenue") == "Thrifty_Megamart"


def test_the_two_fossils_a_half_sells_are_the_two_the_other_half_does_not() -> None:
    # Olivia's shop stocks two of the four and which two is the cartridge's. PokeAPI files all
    # four under both halves, which is the same fault it has about Sinnoh's two - so the rows
    # are refused with a reason rather than quietly kept.
    assert set(alola.alola_excluded("sun")) == {"shieldon", "archen"}
    assert set(alola.alola_excluded("moon")) == {"cranidos", "tirtouga"}

    # Each of the four is still described, because each is handed over in one of the two.
    for species in ("cranidos", "shieldon", "tirtouga", "archen"):
        assert alola.ALOLA_GIFTS[species].kind is GiftKind.FOSSIL

    assert "Skull Fossil" in alola.ALOLA_GIFTS["cranidos"].requirement
    assert "Moon" in alola.alola_excluded("sun")["shieldon"]


def test_the_cosmog_a_half_hands_over_is_handed_over_by_its_own_legendary() -> None:
    # The giver is the Pokemon on the box, so it cannot be shared between the two halves - and
    # the legendary itself is a static in one game and nowhere in the other.
    sun_gifts = alola.alola_gifts("sun")
    moon_gifts = alola.alola_gifts("moon")

    assert sun_gifts["cosmog"].npc == "Solgaleo"
    assert moon_gifts["cosmog"].npc == "Lunala"
    assert "solgaleo" in sun_gifts and "solgaleo" not in moon_gifts
    assert "lunala" in moon_gifts and "lunala" not in sun_gifts


def test_hala_hands_over_all_three_and_the_nursery_hands_over_an_egg() -> None:
    # PokeAPI has one word, "gift", for a starter, a fossil and a present alike, so which of the
    # three a row is comes from the game's own table.
    for species in ("rowlet", "litten", "popplio"):
        assert alola.ALOLA_GIFTS[species].kind is GiftKind.STARTER
        assert alola.ALOLA_GIFTS[species].npc == "Hala"

    # And the one gift in these games that is not a Pokemon when it is handed over.
    assert alola.ALOLA_GIFTS["eevee"].kind is GiftKind.EGG


def test_the_trader_in_tapu_village_hands_over_a_form() -> None:
    # The first trade in this dataset that does. The trader wants a Haunter and gives an Alolan
    # Graveler, which turns into an Alolan Golem the moment it arrives - and "Graveler" on its
    # own would name the wrong rock.
    [rock] = [one for one in alola.ALOLA_TRADES if one.gets == "graveler"]

    assert rock.form == "graveler-alola"
    assert (rock.wants, rock.location, rock.npc) == ("haunter", "Tapu Village", "Sill")

    # The other five hand over a plain species, and the name on each is the original trainer the
    # game stamps on what they give - not the nickname, which a player can change.
    assert [one.gets for one in alola.ALOLA_TRADES if one.form is None] == [
        "machop",
        "bounsweet",
        "happiny",
        "steenee",
        "talonflame",
    ]
    assert all(one.npc for one in alola.ALOLA_TRADES)


def test_both_halves_of_the_alola_pair_show_the_cover_the_picker_will_draw() -> None:
    registry = default_registry()

    assert registry.box_art_of("sun") == "Sun EN boxart.png"
    assert registry.box_art_of("moon") == "Moon EN boxart.png"
