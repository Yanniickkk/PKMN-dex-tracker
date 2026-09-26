"""Which forms of a species get an entry of their own, and in which games.

The app has had four switches for this since Phase 1 - regional, functional, cosmetic, gender -
and nothing to switch on: ``forms.json`` has been written empty ever since, and every game's
step 2 has been deferring to it. This is that table.

PokeAPI keeps the answer in three places and each needs its own reading:

* **Varieties** on the species are separate Pokemon with their own stats: Rotom's appliances,
  Wormadam's cloaks, the Therian trio, Kyurem's fusions.
* **Forms** under a Pokemon are one Pokemon wearing several faces: Unown's letters, Deerling's
  seasons, Shellos's two seas. Walking the varieties and then each variety's forms covers both
  shapes without having to know which one a species uses.
* **A flag and nothing else**: ``has_gender_differences``. Ninety-odd species in the first five
  generations have one and none of them has an entry anywhere - there are two sprites and a
  boolean.

Two questions the source cannot answer, and this module has to:

**Which kind it is.** There is no field for it, and the four switches are the whole point of
the table. It is worked out rather than listed: a form whose typing, base stats or abilities
differ from the species' own is functional, and one that differs in none of them is cosmetic.
That is why Unown's letters come out cosmetic and Wormadam's cloaks functional without anybody
deciding it twice - the letters are one Pokemon with 28 faces and the cloaks are three Pokemon.

**Which games it is in.** A form carries the version group it arrived in, which is most of the
answer: Rotom's appliances say ``platinum``, Therian Landorus says ``black-2-white-2``, and
everything from Generation 6 onward falls outside this dataset and drops out by itself. What
the version group cannot say is a form that arrived and then went no further, which is what
:data:`ONLY_IN` is for.

Three kinds of form are left out on purpose, because none of them is a second Pokemon to catch:

* **Battle-only**, which the source does flag: Castform's weather, Cherrim's sunshine,
  Darmanitan's Zen Mode, Meloetta's Pirouette. They last until the battle ends.
* **Held-item**, which it does not: Arceus's seventeen plates and Genesect's four drives. Take
  the item off and the Pokemon is the same Pokemon again, so counting them would ask a player
  to catch one Arceus eighteen times.
* **Invisible**, which it does not either: Scatterbug's and Spewpa's twenty patterns and
  Mothim's three cloaks are internal values carried forward to decide what something evolves
  into. A player holding all twenty Scatterbug could not tell them apart.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from .models import DexTarget, Form, FormKind, PokemonType, Species
from .pokeapi import PokeApiClient, game_id_of

log = logging.getLogger(__name__)

#: Form names that mean a regional variant rather than anything else.
#:
#: None of them is in the first five generations - the earliest is Alola - and they are named
#: here anyway, because the day one arrives it should land in the right switch rather than be
#: measured by its stats like an ordinary form.
REGIONAL = frozenset({"alola", "galar", "hisui", "paldea"})

#: Form names that are the gender difference PokeAPI models as a form rather than as a flag.
#:
#: Only Frillish and Jellicent do this. Every other species with visible sexes carries a
#: boolean and no form at all, which :func:`gender_forms` answers instead.
GENDERED = frozenset({"male", "female"})

#: The version group from which a gender difference is worth an entry.
#:
#: Generation 4 is where the games started drawing the sexes differently. A female Venusaur has
#: had a narrower stripe since Diamond and Pearl and looks exactly like a male one in Red, so
#: an entry for it in a Kanto collection would be an entry for something nobody can see.
GENDER_FROM = "diamond-pearl"

#: Forms that exist only while an item is held, which is not a second Pokemon to catch.
#:
#: Two species, twenty-one forms, and both of them are Mythical Pokemon that no game in this
#: dataset produces anyway. Written by species rather than by form because that is the shape of
#: the fact: it is Arceus's plates and Genesect's drives, not a list of twenty-one accidents.
HELD_ITEM_FORMS = frozenset({"arceus", "genesect"})

#: Forms that are an internal value and nothing anybody can see.
#:
#: The third kind left out on purpose, and the one that is hardest to notice, because the source
#: models these exactly as it models a Shellos's two seas. Bulbapedia settles all three in its
#: own words: Scatterbug and Spewpa "each have 20 visually indistinct forms" whose only job is
#: to decide which Vivillon they become, and a Mothim keeps the cloak of the Burmy it evolved
#: from "though this is only shown in its internal data".
#:
#: So forty entries, none of which a player could tell apart if they had all of them in a box,
#: and every one of which would have been a tile in the grid asking to be filled. They arrived
#: the day Ultra Sun and Ultra Moon were registered, because that is the version group the
#: source stamps them with - which is the other reason they are easy to miss: they look like
#: something the new games brought.
#:
#: The line this draws is the same one :data:`HELD_ITEM_FORMS` draws, put another way. A form
#: earns an entry when having it is different from not having it. A Vivillon's pattern earns
#: one; the Scatterbug that was always going to become it does not.
INVISIBLE_FORMS = frozenset({"scatterbug", "spewpa", "mothim"})

#: Games no version group can speak for, because their boxes hold a list rather than a series.
#:
#: :meth:`VersionGroupGames.from_group_on` works on one rule - a form arriving in a version
#: group is in that group's games and in every game after them, as long as the species is old
#: enough for the game to have it. That rule has held for twenty-eight games because every one
#: of them can hold anything up to its own National Dex number, so "old enough" is the whole
#: question.
#:
#: Let's Go, Pikachu! and Let's Go, Eevee! break it. They came out after Ultra Sun and Ultra
#: Moon and they hold 153 species: Kanto's 151, Meltan and Melmetal. Left to the rule, every
#: form of every Pokemon in the dataset would be listed as theirs - Deerling's four seasons,
#: the Totem Pokemon of an island they have never heard of, a Therian Landorus - because each
#: of those arrived in an earlier group and Let's Go is later than all of them. The first build
#: that registered these two added 578 lines to the form table, and almost none of them were
#: true.
#:
#: So the rule is switched off for them and the answer will be written out by hand, which is
#: what step 8 is for. Until then the table says these two have no forms at all. That is also
#: not true - a Let's Go player's Alolan Rattata is the whole point of the GO Park, and the
#: partner Pikachu and Eevee are forms nothing else has - but it is the harmless direction to
#: be wrong in: a form the table leaves out is a tile that is not drawn, and a form it invents
#: is a tile asking a player to fill something their game cannot produce.
#:
#: **Sword and Shield break it the same way, and from here on it stays broken.** Let's Go looked
#: like an oddity - a pair of remakes on a console the generation did not belong to - and
#: Generation 8's own first pair does the same thing deliberately: their boxes hold the Galar,
#: Isle of Armor and Crown Tundra Pokedexes and a short list of strangers, which is the change
#: fans named Dexit. Left to the rule they would be handed 373 forms across 746 lines, 92 of
#: them rows this table does not hold at all - every Vivillon pattern, every Unown letter, every
#: Burmy cloak, none of whose species these games have ever met.
#:
#: Nineteen Alolan forms are in that 373 and they are the part step 8 will have to look at
#: hardest, because the rule is closer to right about them than about anything else: Bulbapedia
#: says every regional form of a species these games are compatible with is compatible too, and
#: Raichu, Vulpix, Meowth, Marowak and Sandshrew are all in a Galar list. Closer to right is not
#: right, and which of the nineteen survives is that step's answer rather than this one's.
#:
#: **Brilliant Diamond and Shining Pearl break it for a third reason, and it is the one that
#: shows the rule was never about Dexit.** These two do hold everything up to a National Dex
#: number - 493, the way Diamond did - so the sentence that explains Galar does not apply, and
#: the rule should have been right. Registering them at step 1 handed them 373 forms anyway, the
#: same count and almost the same list: every Alcremie sweet, an Eternamax Eternatus, thirty-six
#: regional forms. The reason is the one thing the rule reads, which is *when* a form arrived:
#: these came out after Sword and Shield, so everything is old enough, and being old enough has
#: nothing to do with it. Bulbapedia states the real limit in a line - only Pokemon that exist
#: in the game data, the first four generations, regional forms excluded.
#:
#: So a remake is the clearest case of all: **what a game holds is a fact about the game, and a
#: date is not a substitute for it.** Off for these two as well, and step 8 writes the answer.
#:
#: **Scarlet and Violet are Galar's case again, and this time the cost was measured at step 1
#: rather than guessed at.** Registering the pair before either half had a single Pokedex entry
#: moved the form table by itself: **eighteen new rows and 396 existing ones gaining two games
#: each**, which is every form in the dataset old enough to qualify. A Galarian Corsola, a
#: Hisuian Zoroark, every Vivillon pattern - none of which these two have ever met. The
#: eighteen new ones are Generation 9's own and mostly real, which is what makes the rest
#: dangerous: the rule is not uniformly wrong here, it is right about a handful and wrong about
#: four hundred.
#:
#: Off for both, and step 8 writes a table for them the way it did for Galar. The eighteen
#: vanish with the rest until it does - a form the table leaves out is a tile that is not drawn,
#: and this is the direction to be wrong in.
FORMS_NAMED_BY_THE_GAME = frozenset(
    {
        "lets-go-pikachu",
        "lets-go-eevee",
        "sword",
        "shield",
        "brilliant-diamond",
        "shining-pearl",
        "legends-arceus",
        "legends-z-a",
        "scarlet",
        "violet",
    }
)

#: The two halves, spelled here so the table below can say "both" in one word.
LETS_GO = ("lets-go-pikachu", "lets-go-eevee")

#: What the Let's Go pair holds, which is step 8's answer to the question this file cannot ask.
#:
#: :data:`FORMS_NAMED_BY_THE_GAME` switches the version-group rule off for those two and says
#: the answer would be written out by hand. This is it: 53 entries, added to whatever the rule
#: worked out rather than replacing it, which is the difference between this and :data:`ONLY_IN`.
#:
#: **The fourteen Alolan forms each half has, and the four that differ, are the eight traders'
#: doing.** Every in-game trade in this pair hands over an Alolan form and nothing else: six of
#: the eight stand in both halves, and two of them - the Camper in Celadon City and the Punk Guy
#: on Cinnabar Island - hand over a different Pokemon depending on which cartridge is in the
#: Switch. What those six and two hand over, and whatever it evolves into, is the whole of what
#: either half can produce. Everything else Alolan comes through the GO Park or from another
#: player, and a form has no dex entry to carry a reason on, so it is left out: a form the table
#: leaves out is a tile that is not drawn, and a form it invents is a tile nobody can fill.
#:
#: **The partner is a form and it belongs to one half each.** PokeAPI calls them
#: ``pikachu-starter`` and ``eevee-starter``, stamps both with this pair's version group, and
#: nothing in the dataset is newer - so the rule would have given them no games at all and
#: dropped them. They are the reason both these games exist.
#:
#: **And both sexes of twenty-three species**, which is what the Generation 4 rule would have
#: said anyway if it had been allowed to speak for these two. Twenty-two of the twenty-three are
#: drawn twice on the wiki's Let's Go sheet; the twenty-third is Eevee, which is drawn once
#: there and once on the Alola sheet as well - the same disagreement with PokeAPI that the
#: Generation 7 scrape turned up, arriving a second time.
LETS_GO_FORMS: Mapping[str, tuple[str, ...]] = {
    "pikachu-starter": ("lets-go-pikachu",),
    "eevee-starter": ("lets-go-eevee",),
    # The six traders both halves have, and what their Pokemon evolve into.
    **dict.fromkeys(
        (
            "rattata-alola",
            "raticate-alola",
            "diglett-alola",
            "dugtrio-alola",
            "geodude-alola",
            "graveler-alola",
            "golem-alola",
            "raichu-alola",
            "marowak-alola",
            "exeggutor-alola",
        ),
        LETS_GO,
    ),
    # The Camper wants a Sandshrew here and the Punk Guy a Grimer.
    **dict.fromkeys(
        ("sandshrew-alola", "sandslash-alola", "grimer-alola", "muk-alola"),
        ("lets-go-pikachu",),
    ),
    # And a Vulpix and a Meowth there.
    **dict.fromkeys(
        ("vulpix-alola", "ninetales-alola", "meowth-alola", "persian-alola"),
        ("lets-go-eevee",),
    ),
    **dict.fromkeys(
        (
            "alakazam-female",
            "butterfree-female",
            "dodrio-female",
            "doduo-female",
            "eevee-female",
            "gloom-female",
            "golbat-female",
            "goldeen-female",
            "gyarados-female",
            "hypno-female",
            "kadabra-female",
            "magikarp-female",
            "pikachu-female",
            "raichu-female",
            "raticate-female",
            "rattata-female",
            "rhydon-female",
            "rhyhorn-female",
            "scyther-female",
            "seaking-female",
            "venusaur-female",
            "vileplume-female",
            "zubat-female",
        ),
        LETS_GO,
    ),
}

#: The two halves, spelled here so the table below can say "both" in one word.
GALAR = ("sword", "shield")

#: What Sword and Shield hold, which is step 8's answer to the question this file cannot ask.
#:
#: 181 entries, added to whatever the rule worked out rather than replacing it, the same way
#: :data:`LETS_GO_FORMS` is. Nothing was remembered into this table; each of the three parts was
#: measured, and the parts answer different kinds of form.
#:
#: **What the games place, they place: 45 forms have an encounter row of their own** under one of
#: the six Sword and Shield version names. A form is a Pokemon in the source and a Pokemon has
#: encounters, so asking each candidate settles every form that is met rather than made - the
#: Galarian Ponyta that is Shield's, the Galarian Farfetch'd that is Sword's, Rotom's five
#: appliances, both Basculin stripes, three of Pumpkaboo's four sizes.
#:
#: **The sexes come off the sprite sheet**, which is a better witness than any rule: a species
#: the Archives draw twice under ``_m`` and ``_f`` is a species these games draw apart, and 54 of
#: them are. Not an encounter's business - a sex is something you look for while catching, so an
#: encounter table places a female Meowstic in Shield and not in Sword and that says nothing
#: about Sword. Read back out of the http cache rather than off a build log, because a name the
#: cache already remembers as missing is never requested again and so never appears in one.
#:
#: **And the rest are written by hand, because they are changed into or evolved into**: the two
#: Galarica items that make a Galarian Slowbro and Slowking, Type: Null's seventeen memories,
#: Kubfu's second tower, the Reins of Unity's two riders, and Alcremie's sixty-two faces, which
#: are one spin with a different sweet in hand.
#:
#: **No Gigantamax form is here and none was excluded by hand.** The source marks them
#: battle-only and :func:`_form` refuses those wherever they come from, which is the same
#: sentence that keeps every Mega out. A Gigantamax Pokemon reverts when the battle ends, and a
#: living dex is about what a box can hold.
GALAR_FORMS: Mapping[str, tuple[str, ...]] = {
    # The regional forms both halves have: eighteen Galarian and eleven Alolan, less the six the
    # halves split. The Alolan ones are the Diglett Trainer's seven rewards and what they evolve
    # into, which is the whole of what Alola left in Galar.
    **dict.fromkeys(
        (
            "articuno-galar", "diglett-alola", "dugtrio-alola", "exeggutor-alola",
            "linoone-galar", "marowak-alola", "meowth-alola", "meowth-galar", "moltres-galar",
            "mr-mime-galar", "persian-alola", "raichu-alola", "sandshrew-alola",
            "ninetales-alola", "sandslash-alola", "slowbro-galar", "slowking-galar",
            "slowpoke-galar",
            "stunfisk-galar", "vulpix-alola", "weezing-galar", "yamask-galar", "zapdos-galar",
            "zigzagoon-galar",
        ),
        GALAR,
    ),
    # The sexes, by the Generation 4 rule rather than off the sheet: a species drawn apart
    # since Diamond is drawn apart here, and a sprite sheet is a witness about drawing
    # rather than about the game. Fifty-four of these are drawn twice on `8s`; Croagunk,
    # Octillery, Politoed, Quagsire and Toxicroak are not, and those five fall back to the
    # shared set's female, which is the right Pokemon in another generation's style.
    **dict.fromkeys(
        (
            "abomasnow-female", "alakazam-female", "butterfree-female", "combee-female",
            "croagunk-female", "eevee-female", "frillish-female", "gabite-female",
            "garchomp-female", "gible-female", "gloom-female", "golbat-female", "goldeen-female",
            "gyarados-female", "heracross-female", "hippopotas-female", "hippowdon-female",
            "indeedee-female", "jellicent-female", "kadabra-female", "ludicolo-female",
            "luxio-female", "luxray-female", "magikarp-female", "mamoswine-female",
            "meowstic-female", "milotic-female", "nuzleaf-female", "octillery-female",
            "pikachu-female", "piloswine-female", "politoed-female", "quagsire-female",
            "raichu-female", "relicanth-female", "rhydon-female", "rhyhorn-female",
            "rhyperior-female", "roselia-female", "roserade-female", "scizor-female",
            "scyther-female", "seaking-female", "shiftry-female", "shinx-female",
            "sneasel-female", "snover-female", "steelix-female", "sudowoodo-female",
            "tangrowth-female", "toxicroak-female", "unfezant-female", "venusaur-female",
            "vileplume-female", "weavile-female", "wobbuffet-female", "wooper-female",
            "xatu-female", "zubat-female",
        ),
        GALAR,
    ),
    # Alcremie, which is one form change wearing sixty-two faces: a cream from how the spin was
    # done and a sweet from what was in hand.
    **dict.fromkeys(
        (
            "alcremie-caramel-swirl-berry-sweet", "alcremie-caramel-swirl-clover-sweet",
            "alcremie-caramel-swirl-flower-sweet", "alcremie-caramel-swirl-love-sweet",
            "alcremie-caramel-swirl-ribbon-sweet", "alcremie-caramel-swirl-star-sweet",
            "alcremie-caramel-swirl-strawberry-sweet", "alcremie-lemon-cream-berry-sweet",
            "alcremie-lemon-cream-clover-sweet", "alcremie-lemon-cream-flower-sweet",
            "alcremie-lemon-cream-love-sweet", "alcremie-lemon-cream-ribbon-sweet",
            "alcremie-lemon-cream-star-sweet", "alcremie-lemon-cream-strawberry-sweet",
            "alcremie-matcha-cream-berry-sweet", "alcremie-matcha-cream-clover-sweet",
            "alcremie-matcha-cream-flower-sweet", "alcremie-matcha-cream-love-sweet",
            "alcremie-matcha-cream-ribbon-sweet", "alcremie-matcha-cream-star-sweet",
            "alcremie-matcha-cream-strawberry-sweet", "alcremie-mint-cream-berry-sweet",
            "alcremie-mint-cream-clover-sweet", "alcremie-mint-cream-flower-sweet",
            "alcremie-mint-cream-love-sweet", "alcremie-mint-cream-ribbon-sweet",
            "alcremie-mint-cream-star-sweet", "alcremie-mint-cream-strawberry-sweet",
            "alcremie-rainbow-swirl-berry-sweet", "alcremie-rainbow-swirl-clover-sweet",
            "alcremie-rainbow-swirl-flower-sweet", "alcremie-rainbow-swirl-love-sweet",
            "alcremie-rainbow-swirl-ribbon-sweet", "alcremie-rainbow-swirl-star-sweet",
            "alcremie-rainbow-swirl-strawberry-sweet", "alcremie-ruby-cream-berry-sweet",
            "alcremie-ruby-cream-clover-sweet", "alcremie-ruby-cream-flower-sweet",
            "alcremie-ruby-cream-love-sweet", "alcremie-ruby-cream-ribbon-sweet",
            "alcremie-ruby-cream-star-sweet", "alcremie-ruby-cream-strawberry-sweet",
            "alcremie-ruby-swirl-berry-sweet", "alcremie-ruby-swirl-clover-sweet",
            "alcremie-ruby-swirl-flower-sweet", "alcremie-ruby-swirl-love-sweet",
            "alcremie-ruby-swirl-ribbon-sweet", "alcremie-ruby-swirl-star-sweet",
            "alcremie-ruby-swirl-strawberry-sweet", "alcremie-salted-cream-berry-sweet",
            "alcremie-salted-cream-clover-sweet", "alcremie-salted-cream-flower-sweet",
            "alcremie-salted-cream-love-sweet", "alcremie-salted-cream-ribbon-sweet",
            "alcremie-salted-cream-star-sweet", "alcremie-salted-cream-strawberry-sweet",
            "alcremie-vanilla-cream-berry-sweet", "alcremie-vanilla-cream-clover-sweet",
            "alcremie-vanilla-cream-flower-sweet", "alcremie-vanilla-cream-love-sweet",
            "alcremie-vanilla-cream-ribbon-sweet", "alcremie-vanilla-cream-star-sweet",
        ),
        GALAR,
    ),
    # Type: Null's memories, which the League Staff member hands over with it.
    **dict.fromkeys(
        (
            "silvally-bug", "silvally-dark", "silvally-dragon", "silvally-electric",
            "silvally-fairy", "silvally-fighting", "silvally-fire", "silvally-flying",
            "silvally-ghost", "silvally-grass", "silvally-ground", "silvally-ice",
            "silvally-poison", "silvally-psychic", "silvally-rock", "silvally-steel",
            "silvally-water",
        ),
        GALAR,
    ),
    # And the rest both halves have, the last two of them faces Galar invented: a Sinistea with
    # a mark under its base, and what a Cracked Pot makes of that one.
    **dict.fromkeys(
        (
            "sinistea-antique", "polteageist-antique", "basculin-blue-striped",
            "calyrex-ice", "calyrex-shadow", "gourgeist-large",
            "gourgeist-small", "gourgeist-super", "lycanroc-dusk", "lycanroc-midnight",
            "pumpkaboo-large", "pumpkaboo-small", "pumpkaboo-super", "rockruff-own-tempo",
            "rotom-fan", "rotom-frost", "rotom-heat", "rotom-mow", "rotom-wash",
            "toxtricity-low-key", "urshifu-rapid-strike",
        ),
        GALAR,
    ),
    # Sword's three, which are Galarian Darumaka, what it becomes, and Galarian Farfetch'd.
    **dict.fromkeys(
        ("darmanitan-galar-standard", "darumaka-galar", "farfetchd-galar"),
        ("sword",),
    ),
    # And Shield's three: Galarian Ponyta, what it becomes, and Galarian Corsola.
    **dict.fromkeys(
        ("corsola-galar", "ponyta-galar", "rapidash-galar"),
        ("shield",),
    ),
}

#: Every form a game names for itself, which is two pairs now and will be every pair after them.
#:
#: Merged rather than chained, because a form can be in both tables and mean both: an Alolan
#: Raichu is one of Let's Go's eight traders' and one of the Diglett Trainer's rewards, and
#: taking either table's answer alone would lose the other's games.
#: The two halves of the Sinnoh remake, spelled here so the table below can say "both".
BDSP = ("brilliant-diamond", "shining-pearl")

#: What Brilliant Diamond and Shining Pearl hold, which is Platinum's list and Diamond's games.
#:
#: **137 forms, and the shape of the answer is the whole finding: this is Diamond's 130 plus
#: the seven Platinum added.** Not the generation's, not the console's - the third version's.
#: Every one of the seven was checked on the wiki rather than carried over:
#:
#: * **Rotom's five appliances** are in Rotom's Room in the Team Galactic Eterna Building, which
#:   the Secret Key opens, exactly as in Platinum;
#: * **Giratina's Origin Forme** is the Griseous Orb - "from Platinum to Brilliant Diamond and
#:   Shining Pearl, it transforms into its Origin Forme while holding a Griseous Orb";
#: * **Shaymin's Sky Forme** is the Gracidea, which the wiki files under Generation VIII key
#:   items for these games.
#:
#: And what is *not* here matters as much. **No regional form of anything**, which is not a
#: judgement call: Bulbapedia states that only Pokemon that exist in the game data - the first
#: four generations, regional forms excluded - can be transferred in at all. No Mega, no
#: Gigantamax, no form from a species above 493.
#:
#: The sexes are the same 94 Diamond has, for the same reason: the rule is Generation 4's, the
#: species are the same species, and a remake redraws them rather than re-deciding them.
BDSP_FORMS: dict[str, tuple[str, ...]] = {
    "abomasnow-female": BDSP,
    "aipom-female": BDSP,
    "alakazam-female": BDSP,
    "ambipom-female": BDSP,
    "beautifly-female": BDSP,
    "bibarel-female": BDSP,
    "bidoof-female": BDSP,
    "blaziken-female": BDSP,
    "buizel-female": BDSP,
    "burmy-sandy": BDSP,
    "burmy-trash": BDSP,
    "butterfree-female": BDSP,
    "cacturne-female": BDSP,
    "camerupt-female": BDSP,
    "combee-female": BDSP,
    "combusken-female": BDSP,
    "croagunk-female": BDSP,
    "deoxys-attack": BDSP,
    "deoxys-defense": BDSP,
    "deoxys-speed": BDSP,
    "dodrio-female": BDSP,
    "doduo-female": BDSP,
    "donphan-female": BDSP,
    "dustox-female": BDSP,
    "eevee-female": BDSP,
    "finneon-female": BDSP,
    "floatzel-female": BDSP,
    "gabite-female": BDSP,
    "garchomp-female": BDSP,
    "gastrodon-east": BDSP,
    "gible-female": BDSP,
    "girafarig-female": BDSP,
    "giratina-origin": BDSP,
    "gligar-female": BDSP,
    "gloom-female": BDSP,
    "golbat-female": BDSP,
    "goldeen-female": BDSP,
    "gulpin-female": BDSP,
    "gyarados-female": BDSP,
    "heracross-female": BDSP,
    "hippopotas-female": BDSP,
    "hippowdon-female": BDSP,
    "houndoom-female": BDSP,
    "hypno-female": BDSP,
    "kadabra-female": BDSP,
    "kricketot-female": BDSP,
    "kricketune-female": BDSP,
    "ledian-female": BDSP,
    "ledyba-female": BDSP,
    "ludicolo-female": BDSP,
    "lumineon-female": BDSP,
    "luxio-female": BDSP,
    "luxray-female": BDSP,
    "magikarp-female": BDSP,
    "mamoswine-female": BDSP,
    "medicham-female": BDSP,
    "meditite-female": BDSP,
    "meganium-female": BDSP,
    "milotic-female": BDSP,
    "murkrow-female": BDSP,
    "numel-female": BDSP,
    "nuzleaf-female": BDSP,
    "octillery-female": BDSP,
    "pachirisu-female": BDSP,
    "pikachu-female": BDSP,
    "piloswine-female": BDSP,
    "politoed-female": BDSP,
    "quagsire-female": BDSP,
    "raichu-female": BDSP,
    "raticate-female": BDSP,
    "rattata-female": BDSP,
    "relicanth-female": BDSP,
    "rhydon-female": BDSP,
    "rhyhorn-female": BDSP,
    "rhyperior-female": BDSP,
    "roselia-female": BDSP,
    "roserade-female": BDSP,
    "rotom-fan": BDSP,
    "rotom-frost": BDSP,
    "rotom-heat": BDSP,
    "rotom-mow": BDSP,
    "rotom-wash": BDSP,
    "scizor-female": BDSP,
    "scyther-female": BDSP,
    "seaking-female": BDSP,
    "shaymin-sky": BDSP,
    "shellos-east": BDSP,
    "shiftry-female": BDSP,
    "shinx-female": BDSP,
    "sneasel-female": BDSP,
    "snover-female": BDSP,
    "staraptor-female": BDSP,
    "staravia-female": BDSP,
    "starly-female": BDSP,
    "steelix-female": BDSP,
    "sudowoodo-female": BDSP,
    "swalot-female": BDSP,
    "tangrowth-female": BDSP,
    "torchic-female": BDSP,
    "toxicroak-female": BDSP,
    "unown-b": BDSP,
    "unown-c": BDSP,
    "unown-d": BDSP,
    "unown-e": BDSP,
    "unown-exclamation": BDSP,
    "unown-f": BDSP,
    "unown-g": BDSP,
    "unown-h": BDSP,
    "unown-i": BDSP,
    "unown-j": BDSP,
    "unown-k": BDSP,
    "unown-l": BDSP,
    "unown-m": BDSP,
    "unown-n": BDSP,
    "unown-o": BDSP,
    "unown-p": BDSP,
    "unown-q": BDSP,
    "unown-question": BDSP,
    "unown-r": BDSP,
    "unown-s": BDSP,
    "unown-t": BDSP,
    "unown-u": BDSP,
    "unown-v": BDSP,
    "unown-w": BDSP,
    "unown-x": BDSP,
    "unown-y": BDSP,
    "unown-z": BDSP,
    "ursaring-female": BDSP,
    "venusaur-female": BDSP,
    "vileplume-female": BDSP,
    "weavile-female": BDSP,
    "wobbuffet-female": BDSP,
    "wooper-female": BDSP,
    "wormadam-sandy": BDSP,
    "wormadam-trash": BDSP,
    "xatu-female": BDSP,
    "zubat-female": BDSP,
}


#: The one game in Hisui, spelled so the table below can say it in one word.
HISUI = ("legends-arceus",)

#: What Legends: Arceus holds, which is step 8's answer to the question this file cannot ask.
#:
#: **The rule gave this game 393 forms and it has 117.** Every Alcremie sweet, nineteen Alolan
#: forms, eighteen Galarian ones - because all the rule reads is *when* a form arrived, and this
#: game came out after all of them. It is the fourth game in a row the rule is wrong about and
#: the reason is the same one Sword and Shield wrote down: what a game holds is a fact about the
#: game, and a date is no substitute for it.
#:
#: **Read off the sheet rather than argued about.** The Archives keep 367 files under "Legends:
#: Arceus models", one per thing the game draws, and the category pages out on a url the
#: Archives' robots.txt allows - which the reading before these six games had written off. Every
#: number in it is one of the Hisui Pokedex's 242 and every letter code in it is a form. So the
#: list below is what the game's own models say, not what a version group implies:
#:
#: * **eighteen regional forms** - the sixteen Hisuian ones, and the Alolan Vulpix and Ninetales
#:   that Request 83 hands over. Nothing else Alolan or Galarian is drawn at all, which is the
#:   third source to say so after the request and HOME's transfer rule;
#: * **eleven functional** - three Origin Formes, four Therian Formes, Sky Shaymin, the
#:   White-Striped Basculin and Wormadam's two other cloaks;
#: * **twenty-seven Unown** and four cosmetic - Burmy's two other cloaks, and the east sea
#:   Shellos and Gastrodon;
#: * **fifty-seven sexes**, which is what the sheet draws twice.
#:
#: **What is left out, and it is the one thing the sheet does not settle: Rotom's five
#: appliances.** The models are there - ``Spr_8a_479F``, ``L``, ``O``, ``R``, ``W`` - and each
#: has a Pokedex entry written for this game, a cauldron and a bureau and a cupboard instead of
#: a microwave and a washing machine, and Bulbapedia says the forms were documented in the Hisui
#: Pokedex by Professor Laventon. What nothing found says is how a player changes one, and this
#: game has no Rotom Room and no appliances to possess. A form whose sentence cannot be written
#: is a tile nobody can fill, which is the call :data:`LETS_GO_FORMS` already made, so the five
#: are out until somebody reads the mechanism. One line to add them the day it is read.
HISUI_FORMS: dict[str, tuple[str, ...]] = {
    "abomasnow-female": HISUI,
    "aipom-female": HISUI,
    "alakazam-female": HISUI,
    "ambipom-female": HISUI,
    "arcanine-hisui": HISUI,
    "avalugg-hisui": HISUI,
    "basculegion-female": HISUI,
    "basculin-white-striped": HISUI,
    "beautifly-female": HISUI,
    "bibarel-female": HISUI,
    "bidoof-female": HISUI,
    "braviary-hisui": HISUI,
    "burmy-sandy": HISUI,
    "burmy-trash": HISUI,
    "combee-female": HISUI,
    "croagunk-female": HISUI,
    "decidueye-hisui": HISUI,
    "dialga-origin": HISUI,
    "dustox-female": HISUI,
    "eevee-female": HISUI,
    "electrode-hisui": HISUI,
    "enamorus-therian": HISUI,
    "finneon-female": HISUI,
    "floatzel-female": HISUI,
    "gabite-female": HISUI,
    "garchomp-female": HISUI,
    "gastrodon-east": HISUI,
    "gible-female": HISUI,
    "giratina-origin": HISUI,
    "gligar-female": HISUI,
    "golbat-female": HISUI,
    "goodra-hisui": HISUI,
    "growlithe-hisui": HISUI,
    "gyarados-female": HISUI,
    "heracross-female": HISUI,
    "hippopotas-female": HISUI,
    "hippowdon-female": HISUI,
    "kadabra-female": HISUI,
    "kricketot-female": HISUI,
    "kricketune-female": HISUI,
    "landorus-therian": HISUI,
    "lilligant-hisui": HISUI,
    "lumineon-female": HISUI,
    "luxio-female": HISUI,
    "luxray-female": HISUI,
    "magikarp-female": HISUI,
    "mamoswine-female": HISUI,
    "murkrow-female": HISUI,
    "ninetales-alola": HISUI,
    "octillery-female": HISUI,
    "pachirisu-female": HISUI,
    "palkia-origin": HISUI,
    "pikachu-female": HISUI,
    "piloswine-female": HISUI,
    "qwilfish-hisui": HISUI,
    "raichu-female": HISUI,
    "rhydon-female": HISUI,
    "rhyhorn-female": HISUI,
    "rhyperior-female": HISUI,
    "roselia-female": HISUI,
    "roserade-female": HISUI,
    "samurott-hisui": HISUI,
    "scizor-female": HISUI,
    "scyther-female": HISUI,
    "shaymin-sky": HISUI,
    "shellos-east": HISUI,
    "shinx-female": HISUI,
    "sliggoo-hisui": HISUI,
    "sneasel-female": HISUI,
    "sneasel-hisui": HISUI,
    "snover-female": HISUI,
    "staraptor-female": HISUI,
    "staravia-female": HISUI,
    "starly-female": HISUI,
    "steelix-female": HISUI,
    "sudowoodo-female": HISUI,
    "tangrowth-female": HISUI,
    "thundurus-therian": HISUI,
    "tornadus-therian": HISUI,
    "toxicroak-female": HISUI,
    "typhlosion-hisui": HISUI,
    "unown-b": HISUI,
    "unown-c": HISUI,
    "unown-d": HISUI,
    "unown-e": HISUI,
    "unown-exclamation": HISUI,
    "unown-f": HISUI,
    "unown-g": HISUI,
    "unown-h": HISUI,
    "unown-i": HISUI,
    "unown-j": HISUI,
    "unown-k": HISUI,
    "unown-l": HISUI,
    "unown-m": HISUI,
    "unown-n": HISUI,
    "unown-o": HISUI,
    "unown-p": HISUI,
    "unown-q": HISUI,
    "unown-question": HISUI,
    "unown-r": HISUI,
    "unown-s": HISUI,
    "unown-t": HISUI,
    "unown-u": HISUI,
    "unown-v": HISUI,
    "unown-w": HISUI,
    "unown-x": HISUI,
    "unown-y": HISUI,
    "unown-z": HISUI,
    "ursaring-female": HISUI,
    "voltorb-hisui": HISUI,
    "vulpix-alola": HISUI,
    "weavile-female": HISUI,
    "wormadam-sandy": HISUI,
    "wormadam-trash": HISUI,
    "zoroark-hisui": HISUI,
    "zorua-hisui": HISUI,
    "zubat-female": HISUI,
}


#: The one game in Lumiose City, spelled so the table below can say it in one word.
ZA = ("legends-z-a",)

#: What Legends: Z-A holds, which is step 8's answer to the question this file cannot ask.
#:
#: **The rule gave this game 420 forms and it has 90** - a margin of 330, where Hisui's was 276
#: and Galar's was the first of the four. It is the fifth game running the rule is wrong about,
#: and by now the rule being wrong is the expected answer rather than the finding.
#:
#: **Most of that margin is not a judgement at all.** Of the 420, only 135 are even forms of a
#: species this game lists - the other 285 belong to species that are in neither the Lumiose
#: Pokedex nor the Hyperspace one, and **only Pokemon in those two lists can be here at all**.
#: So the real question was 135 wide, over 73 species, and that is a list a person can read.
#:
#: **There is no sheet to read it off, which is what makes this game different from Hisui.**
#: The Archives keep 367 files for Legends: Arceus, one per thing it draws; they keep **35** for
#: this game and every one is a Mega. So the list below is assembled from what the game's own
#: sources say it has: its wild tables, its gifts, its evolutions, and the Game locations rows
#: on each species' article. What it comes to:
#:
#: * **sixteen regional forms**, every one of them another region's - four Hisuian, seven
#:   Galarian, four Alolan and Galarian Mr. Mime. **This game introduces none of its own**,
#:   which the wiki states as a fact about it: the first non-remake core series game since
#:   Generation VII not to add a regional form.
#: * **sixteen functional** - Rotom's five appliances, Eternal Flower Floette, the Low Key
#:   Toxtricity, two Tatsugiri, three Gourgeist and three Pumpkaboo sizes, and a Roaming
#:   Gimmighoul.
#: * **seventeen cosmetic** - the Flabebe line's four colours each, the three Squawkabilly
#:   plumages, and two Vivillon.
#: * **forty-one sexes**, which is a fact about the species rather than about the game.
#:
#: **And Rotom's five appliances are in this one**, which is worth saying beside
#: :data:`HISUI_FORMS`: that table leaves them out because nothing said how a player changes
#: one. Here nobody has to change anything - a Heat Rotom is standing in an Electric-type
#: distortion at level 54, and the game's own table says so.
#:
#: **Four things are deliberately left out, and all four are the same call.** Hoopa Unbound,
#: Resolute Keldeo, Original Color Magearna and Furfrou's nine trims each have a Pokedex entry
#: written for this game - and a Pokedex entry is what Hisui's Rotom had too. What none of them
#: has is a sentence saying how a player gets one: no Prison Bottle, no Secret Sword, no
#: groomer, and the Game locations row for each names no form. **A form whose sentence cannot be
#: written is a tile nobody can fill.** Four lines to add them the day somebody reads the
#: mechanism, and Vivillon is the shape of what that reading would look like - seventeen of its
#: nineteen patterns are out for the same reason, and the two that are in are in because the
#: game produces them: a Garden Pattern in Wild Zone tables and the Marine Pattern the museum's
#: Spewpa evolves into.
#:
#: **Two more are out for a reason the game states about itself**: abilities are not featured
#: here, so a Battle Bond Greninja and Zygarde's two Power Construct formes cannot be what they
#: are. That is a mechanism the game removed rather than one nobody has read.
ZA_FORMS: dict[str, tuple[str, ...]] = {
    "abomasnow-female": ZA,
    "alakazam-female": ZA,
    "avalugg-hisui": ZA,
    "blaziken-female": ZA,
    "camerupt-female": ZA,
    "combusken-female": ZA,
    "eevee-female": ZA,
    "farfetchd-galar": ZA,
    "flabebe-blue": ZA,
    "flabebe-orange": ZA,
    "flabebe-white": ZA,
    "flabebe-yellow": ZA,
    "floette-blue": ZA,
    "floette-eternal": ZA,
    "floette-orange": ZA,
    "floette-white": ZA,
    "floette-yellow": ZA,
    "florges-blue": ZA,
    "florges-orange": ZA,
    "florges-white": ZA,
    "florges-yellow": ZA,
    "gabite-female": ZA,
    "garchomp-female": ZA,
    "gible-female": ZA,
    "gimmighoul-roaming": ZA,
    "golbat-female": ZA,
    "goodra-hisui": ZA,
    "gourgeist-large": ZA,
    "gourgeist-small": ZA,
    "gourgeist-super": ZA,
    "gulpin-female": ZA,
    "gyarados-female": ZA,
    "heracross-female": ZA,
    "hippopotas-female": ZA,
    "hippowdon-female": ZA,
    "houndoom-female": ZA,
    "indeedee-female": ZA,
    "kadabra-female": ZA,
    "magikarp-female": ZA,
    "marowak-alola": ZA,
    "medicham-female": ZA,
    "meditite-female": ZA,
    "meganium-female": ZA,
    "meowstic-female": ZA,
    "meowth-alola": ZA,
    "meowth-galar": ZA,
    "milotic-female": ZA,
    "mr-mime-galar": ZA,
    "numel-female": ZA,
    "persian-alola": ZA,
    "pikachu-female": ZA,
    "pumpkaboo-large": ZA,
    "pumpkaboo-small": ZA,
    "pumpkaboo-super": ZA,
    "pyroar-female": ZA,
    "qwilfish-hisui": ZA,
    "raichu-alola": ZA,
    "raichu-female": ZA,
    "roselia-female": ZA,
    "roserade-female": ZA,
    "rotom-fan": ZA,
    "rotom-frost": ZA,
    "rotom-heat": ZA,
    "rotom-mow": ZA,
    "rotom-wash": ZA,
    "scizor-female": ZA,
    "scyther-female": ZA,
    "sliggoo-hisui": ZA,
    "slowbro-galar": ZA,
    "slowking-galar": ZA,
    "slowpoke-galar": ZA,
    "snover-female": ZA,
    "squawkabilly-blue-plumage": ZA,
    "squawkabilly-white-plumage": ZA,
    "squawkabilly-yellow-plumage": ZA,
    "staraptor-female": ZA,
    "staravia-female": ZA,
    "starly-female": ZA,
    "steelix-female": ZA,
    "stunfisk-galar": ZA,
    "swalot-female": ZA,
    "tatsugiri-droopy": ZA,
    "tatsugiri-stretchy": ZA,
    "torchic-female": ZA,
    "toxtricity-low-key": ZA,
    "venusaur-female": ZA,
    "vivillon-garden": ZA,
    "vivillon-marine": ZA,
    "yamask-galar": ZA,
    "zubat-female": ZA,
}



#: The two halves, spelled here so the table below can say "both" in one word.
PALDEA = ("scarlet", "violet")

#: What Scarlet and Violet hold, which is step 8's answer to the question this file cannot ask.
#:
#: **170 entries, and not one of them was remembered into this table.** Every part was measured,
#: and the parts answer different kinds of form. The universe to choose from was 273 forms of a
#: species one of the three lists names, plus thirty the table did not hold at all - and nine of
#: those thirty were refused before anybody had to think about them, by the same sentence that
#: keeps every Mega out: a Gulping Cramorant, a Noice Eiscue, a Busted Mimikyu, a Hangry Morpeko,
#: an Ash-Greninja, a Hero Palafin and both Terapagos formes are battle-only, and a living dex is
#: about what a box can hold.
#:
#: **All thirty-six regional forms are in, and the article says so rather than the grass.**
#: "All regional forms of compatible Pokemon that existed at the time of release and their
#: respective regional evolved forms are also compatible" - so an Alolan Raichu belongs in a
#: Paldean box whether or not the Terarium places one. Fifteen of them it does place, which is
#: the Indigo Disk doing what it was built for.
#:
#: **All seventy-five sexes are in, because a sex is a fact about the species.** Galar read its
#: own sprite sheet to decide this and Hisui and Lumiose did not have to; these two draw from
#: Pokemon HOME's set, which is shared, so a sheet would answer a question about HOME rather
#: than about Paldea.
#:
#: **Sixteen functional and thirty-two cosmetic**, and each exclusion has a reason rather than
#: a shrug:
#:
#: * **Alcremie's sixty-two are out because the game has no Sweets.** An Alcremie in Paldea
#:   comes out of a five- or six-star Tera Raid already made, so there is no Milcery to spin
#:   and no cream to choose.
#: * **Minior is in as its seven cores, and step 6 is what settled that.** Step 8 chose the
#:   meteors, because the source's default is ``minior-red-meteor`` and a meteor is what stands
#:   in the overworld. Then the pictures were asked for and Pokemon HOME turned out to draw
#:   **one plain Minior and seven cores, and no coloured meteor at all** - so the meteors would
#:   have been six tiles falling back to another generation's style beside a species drawn from
#:   HOME, to show a difference nobody can see until the shield breaks. The picture set
#:   answered a question the form table could not, which is a thing worth having happened once.
#: * **Seventeen of Vivillon's nineteen patterns are out**, which is Lumiose's call again: only
#:   the Fancy Pattern is in a table here. The others are reachable, and by a route no other
#:   game in this dataset has - a postcard sent from Pokemon GO changes the pattern of wild
#:   Vivillon for a day, according to where in the world the postcard came from. That is a
#:   second app and a physical location, which is the Friend Safari's shape, and a form whose
#:   sentence a player cannot act on is a tile nobody can fill.
#: * **Roaming Form Gimmighoul is out and the reason is exact**: it flees when it is
#:   interacted with and leaves coins behind. It can be caught in Pokemon GO and sent over, and
#:   Pokemon GO is not a game this dataset holds.
#: * The Totem Pokemon, the spiky-eared Pichu, Pikachu's caps, the Let's Go partners, the
#:   Eternal Flower Floette and a Battle Bond Greninja are out because they are somebody else's
#:   game or somebody else's event.
#:
#: **And eleven are Generation IX's own**, which is the part that was invisible until step 1
#: switched the version-group rule off and watched them disappear: Dunsparce's 1% third
#: segment, Tandemaus's 1% third mouse, a female Oinkologne, Ogerpon's three masks, Paldean
#: Tauros's three breeds, Paldean Wooper - and **Bloodmoon Ursaluna**, which closes the sharpest
#: thing step 2 found. Kitakami numbers the Bloodmoon one at #196 and the ordinary Ursaluna is
#: a stranger to all three lists; the entry is still the species, but the form now exists and
#: the tile can be drawn.
#:
#: **Koraidon's four builds and Miraidon's four modes are out**, and it is the one call here
#: that is about a vehicle rather than a Pokemon: they are how the thing a player rides gets
#: over a river, and a box holds one of it.
PALDEA_FORMS: Mapping[str, tuple[str, ...]] = {
    "abomasnow-female": PALDEA,
    "aipom-female": PALDEA,
    "ambipom-female": PALDEA,
    "arcanine-hisui": PALDEA,
    "avalugg-hisui": PALDEA,
    "basculegion-female": PALDEA,
    "basculin-blue-striped": PALDEA,
    "basculin-white-striped": PALDEA,
    "blaziken-female": PALDEA,
    "braviary-hisui": PALDEA,
    "buizel-female": PALDEA,
    "cacturne-female": PALDEA,
    "camerupt-female": PALDEA,
    "combee-female": PALDEA,
    "combusken-female": PALDEA,
    "croagunk-female": PALDEA,
    "decidueye-hisui": PALDEA,
    "deerling-autumn": PALDEA,
    "deerling-summer": PALDEA,
    "deerling-winter": PALDEA,
    "diglett-alola": PALDEA,
    "dodrio-female": PALDEA,
    "doduo-female": PALDEA,
    "donphan-female": PALDEA,
    "dudunsparce-three-segment": PALDEA,
    "dugtrio-alola": PALDEA,
    "eevee-female": PALDEA,
    "electrode-hisui": PALDEA,
    "exeggutor-alola": PALDEA,
    "finneon-female": PALDEA,
    "flabebe-blue": PALDEA,
    "flabebe-orange": PALDEA,
    "flabebe-white": PALDEA,
    "flabebe-yellow": PALDEA,
    "floatzel-female": PALDEA,
    "floette-blue": PALDEA,
    "floette-orange": PALDEA,
    "floette-white": PALDEA,
    "floette-yellow": PALDEA,
    "florges-blue": PALDEA,
    "florges-orange": PALDEA,
    "florges-white": PALDEA,
    "florges-yellow": PALDEA,
    "gabite-female": PALDEA,
    "garchomp-female": PALDEA,
    "gastrodon-east": PALDEA,
    "geodude-alola": PALDEA,
    "gible-female": PALDEA,
    "girafarig-female": PALDEA,
    "gligar-female": PALDEA,
    "gloom-female": PALDEA,
    "golem-alola": PALDEA,
    "goodra-hisui": PALDEA,
    "graveler-alola": PALDEA,
    "grimer-alola": PALDEA,
    "growlithe-hisui": PALDEA,
    "gulpin-female": PALDEA,
    "gyarados-female": PALDEA,
    "heracross-female": PALDEA,
    "hippopotas-female": PALDEA,
    "hippowdon-female": PALDEA,
    "houndoom-female": PALDEA,
    "hypno-female": PALDEA,
    "indeedee-female": PALDEA,
    "kricketot-female": PALDEA,
    "kricketune-female": PALDEA,
    "lilligant-hisui": PALDEA,
    "ludicolo-female": PALDEA,
    "lumineon-female": PALDEA,
    "luxio-female": PALDEA,
    "luxray-female": PALDEA,
    "lycanroc-dusk": PALDEA,
    "lycanroc-midnight": PALDEA,
    "magikarp-female": PALDEA,
    "mamoswine-female": PALDEA,
    "maushold-family-of-three": PALDEA,
    "medicham-female": PALDEA,
    "meditite-female": PALDEA,
    "meganium-female": PALDEA,
    "meowstic-female": PALDEA,
    "meowth-alola": PALDEA,
    "meowth-galar": PALDEA,
    "milotic-female": PALDEA,
    "minior-blue": PALDEA,
    "minior-green": PALDEA,
    "minior-indigo": PALDEA,
    "minior-orange": PALDEA,
    "minior-red": PALDEA,
    "minior-violet": PALDEA,
    "minior-yellow": PALDEA,
    "muk-alola": PALDEA,
    "murkrow-female": PALDEA,
    "ninetales-alola": PALDEA,
    "numel-female": PALDEA,
    "nuzleaf-female": PALDEA,
    "ogerpon-cornerstone-mask": PALDEA,
    "ogerpon-hearthflame-mask": PALDEA,
    "ogerpon-wellspring-mask": PALDEA,
    "oinkologne-female": PALDEA,
    "oricorio-pau": PALDEA,
    "oricorio-pom-pom": PALDEA,
    "oricorio-sensu": PALDEA,
    "pachirisu-female": PALDEA,
    "persian-alola": PALDEA,
    "pikachu-female": PALDEA,
    "piloswine-female": PALDEA,
    "politoed-female": PALDEA,
    "polteageist-antique": PALDEA,
    "pyroar-female": PALDEA,
    "quagsire-female": PALDEA,
    "qwilfish-hisui": PALDEA,
    "raichu-alola": PALDEA,
    "raichu-female": PALDEA,
    "rhydon-female": PALDEA,
    "rhyhorn-female": PALDEA,
    "rhyperior-female": PALDEA,
    "rockruff-own-tempo": PALDEA,
    "rotom-fan": PALDEA,
    "rotom-frost": PALDEA,
    "rotom-heat": PALDEA,
    "rotom-mow": PALDEA,
    "rotom-wash": PALDEA,
    "samurott-hisui": PALDEA,
    "sandshrew-alola": PALDEA,
    "sandslash-alola": PALDEA,
    "sawsbuck-autumn": PALDEA,
    "sawsbuck-summer": PALDEA,
    "sawsbuck-winter": PALDEA,
    "scizor-female": PALDEA,
    "scyther-female": PALDEA,
    "shellos-east": PALDEA,
    "shiftry-female": PALDEA,
    "shinx-female": PALDEA,
    "sinistea-antique": PALDEA,
    "sliggoo-hisui": PALDEA,
    "slowbro-galar": PALDEA,
    "slowking-galar": PALDEA,
    "slowpoke-galar": PALDEA,
    "sneasel-female": PALDEA,
    "sneasel-hisui": PALDEA,
    "snover-female": PALDEA,
    "squawkabilly-blue-plumage": PALDEA,
    "squawkabilly-white-plumage": PALDEA,
    "squawkabilly-yellow-plumage": PALDEA,
    "staraptor-female": PALDEA,
    "staravia-female": PALDEA,
    "starly-female": PALDEA,
    "sudowoodo-female": PALDEA,
    "swalot-female": PALDEA,
    "tatsugiri-droopy": PALDEA,
    "tatsugiri-stretchy": PALDEA,
    "tauros-paldea-aqua-breed": PALDEA,
    "tauros-paldea-blaze-breed": PALDEA,
    "tauros-paldea-combat-breed": PALDEA,
    "torchic-female": PALDEA,
    "toxicroak-female": PALDEA,
    "toxtricity-low-key": PALDEA,
    "typhlosion-hisui": PALDEA,
    "ursaluna-bloodmoon": PALDEA,
    "ursaring-female": PALDEA,
    "venusaur-female": PALDEA,
    "vileplume-female": PALDEA,
    "vivillon-fancy": PALDEA,
    "voltorb-hisui": PALDEA,
    "vulpix-alola": PALDEA,
    "weavile-female": PALDEA,
    "weezing-galar": PALDEA,
    "wooper-female": PALDEA,
    "wooper-paldea": PALDEA,
    "zoroark-hisui": PALDEA,
    "zorua-hisui": PALDEA,
}

NAMED_BY_HAND: Mapping[str, tuple[str, ...]] = {
    slug: tuple(
        sorted(
            {
                *LETS_GO_FORMS.get(slug, ()),
                *GALAR_FORMS.get(slug, ()),
                *BDSP_FORMS.get(slug, ()),
                *HISUI_FORMS.get(slug, ()),
                *ZA_FORMS.get(slug, ()),
                *PALDEA_FORMS.get(slug, ()),
            }
        )
    )
    for slug in {
        *LETS_GO_FORMS,
        *GALAR_FORMS,
        *BDSP_FORMS,
        *HISUI_FORMS,
        *ZA_FORMS,
        *PALDEA_FORMS,
    }
}

#: Where a form is, when the version group it arrived in says more than the truth.
#:
#: The default is that a form reaches every game from its own version group onward, which is
#: right for almost all of them: Rotom's appliances arrived in Platinum and every later game
#: still has them.
#:
#: These are the ones where it is not. Deoxys is the awkward case of the series - each of the
#: three Generation 3 cartridges changes it into a different form, and PokeAPI can only say
#: which version *group* each form belongs to, so FireRed and LeafGreen come out sharing two
#: forms that neither of them shares. The spiky-eared Pichu is the other kind: it is in
#: HeartGold and SoulSilver, it cannot be traded or transferred, and so it goes no further.
#: Every game in this dataset that has a meteorite to change a Deoxys with.
#:
#: Generation 3 decides the forme by the cartridge and there is nothing a player can do about
#: it: a Deoxys is Normal in Ruby and Sapphire, Attack in FireRed, Defense in LeafGreen and
#: Speed in Emerald, and trading it is the only way to see another. From Generation 4 on a
#: meteorite cycles it through all four - outside in Veilstone City, on Route 3 in Johto, in the
#: Nacrene Museum, in Ambrette Town's Fossil Lab, in Professor Cozmo's house in Fallarbor, and
#: beside Sophocles in the Hokulani Observatory on Mount Hokulani.
#:
#: Written out because the version group a form arrived in cannot say it. All three formes
#: arrived with Generation 3 and were pinned to the one cartridge each of them came from, which
#: was right while this dataset held nothing later and wrong from Diamond on.
#:
#: **And it has to be extended by hand every time**, which is the cost of writing it out: Omega
#: Ruby found it missing, Sun and Moon found it missing again, and Ultra Sun and Ultra Moon
#: found it a third time. The meteorite beside Sophocles is one meteorite and all four Alola
#: cartridges walk past it.
METEORITE: tuple[str, ...] = (
    "diamond",
    "pearl",
    "platinum",
    "heartgold",
    "soulsilver",
    "black",
    "white",
    "black-2",
    "white-2",
    "x",
    "y",
    "omega-ruby",
    "alpha-sapphire",
    "sun",
    "moon",
    "ultra-sun",
    "ultra-moon",
)

#: The six Cosplay Pikachu, which never leave the game they were dressed in.
#:
#: Pokemon Bank refuses them and so does a trade. That is not a rule about what Omega Ruby and
#: Alpha Sapphire can produce - they produce all six, at the Contest Halls - but about where one
#: can ever be afterwards, and the answer is nowhere else. A Generation 7 box cannot hold one,
#: so a Generation 7 grid should not have a tile for one.
#:
#: The version group says the opposite, which is what :data:`ONLY_IN` is for. The spiky-eared
#: Pichu was the first of these and looked like a curiosity; with these six it is a kind. A form
#: that cannot be transferred is stuck in its own generation however long the series runs, and a
#: living dex kept anywhere later can never hold one.
COSPLAY_PIKACHU: tuple[str, ...] = (
    "pikachu-cosplay",
    "pikachu-rock-star",
    "pikachu-belle",
    "pikachu-pop-star",
    "pikachu-phd",
    "pikachu-libre",
)

#: The games a form is in, where the version group it arrived in is not the answer.
#:
#: Two kinds of exception, and they pull opposite ways. Deoxys and the meteorite is a form that
#: reaches *further* than its version group suggests: the three formes were pinned to one
#: Generation 3 cartridge each and every game from Diamond on can cycle through all four.
#: :data:`COSPLAY_PIKACHU` and the spiky-eared Pichu are forms that reach *less* far, because
#: nothing will carry them out of the games that made them.
ONLY_IN: Mapping[str, tuple[str, ...]] = {
    "deoxys-attack": ("firered", *METEORITE),
    "deoxys-defense": ("leafgreen", *METEORITE),
    "deoxys-speed": ("emerald", *METEORITE),
    "pichu-spiky-eared": ("heartgold", "soulsilver"),
    **dict.fromkeys(COSPLAY_PIKACHU, ("omega-ruby", "alpha-sapphire")),
}

#: What to call a form on screen, where the slug does not say it well.
#:
#: The app prints "Shellos (West Sea)", so this is the part in brackets rather than the whole
#: name. Everything not named here is its form name with the words capitalised, which is right
#: for Heat, Therian, Summer and eighty others.
LABELS: Mapping[str, str] = {
    # What the Let's Go pair calls the Pikachu and the Eevee it starts a player with. The source
    # spells it "starter", and every other game in the dataset means by that a choice of three.
    "starter": "Partner",
    "exclamation": "!",
    "question": "?",
    "east": "East Sea",
    "west": "West Sea",
    "spiky-eared": "Spiky-eared",
}


@dataclass
class VersionGroupGames:
    """Which games are in each version group, and where each group sits in the series.

    A game id and PokeAPI's version name are the same string for almost every game in this
    dataset, and :data:`pokeapi.VERSION_NAMES` is where the exceptions are written down. The
    check below is what found the first of them: a game the registry knows and the source does
    not would otherwise quietly lose all of its forms, and Legends: Z-A - ``legends-z-a`` here
    and ``legends-za`` there - would have been built without a single one.
    """

    api: PokeApiClient
    game_ids: frozenset[str]
    refresh: bool = False
    _order: dict[str, int] = field(default_factory=dict)
    _games: dict[str, tuple[str, ...]] = field(default_factory=dict)
    _generation: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        listing = self.api.resource("version-group?limit=100", refresh=self.refresh)

        for entry in listing["results"]:
            group = self.api.resource(f"version-group/{entry['name']}", refresh=self.refresh)
            self._order[entry["name"]] = int(group["order"])
            self._games[entry["name"]] = tuple(
                game
                for version in group["versions"]
                if (game := game_id_of(version["name"])) in self.game_ids
            )
            for game in self._games[entry["name"]]:
                self._generation[game] = generation_of(group["generation"]["url"])

        missing = self.game_ids - set(self._generation)
        if missing:
            raise FormsError(
                "these games are not any version group's: " + ", ".join(sorted(missing))
            )

    @property
    def newest_generation(self) -> int:
        """The latest generation any game here belongs to."""
        return max(self._generation.values())

    def knows(self, group: str) -> bool:
        return group in self._order

    def named_by_hand(self, slug: str) -> list[str]:
        """The games a hand-written table gives this form, filtered to the ones being built.

        Filtered because a build of one game is still a build: :data:`NAMED_BY_HAND` names seven
        games and a ``--game red`` build has none of them, and a form that claimed them would
        write a table the rest of the dataset disagrees with.
        """
        return [game for game in NAMED_BY_HAND.get(slug, ()) if game in self._generation]

    def order_of(self, group: str) -> int:
        return self._order[group]

    def from_group_on(self, group: str, *, generation: int) -> list[str]:
        """Every game in that version group or a later one that can hold the species at all.

        Two filters rather than one, and the second is easy to forget. A gender difference
        arrived in Generation 4 and every game from Diamond onward draws it - but only for a
        species those games have. Pyroar's sexes look nothing alike and Pyroar is two
        generations away from the newest game here, so the answer for it is no games at all
        rather than nine.

        Three, in fact, and the third is a whole game rather than a species:
        :data:`FORMS_NAMED_BY_THE_GAME` is the games this reasoning does not describe at all.
        """
        here = self.order_of(group)

        return sorted(
            game
            for name, games in self._games.items()
            if self._order[name] >= here
            for game in games
            if self._generation[game] >= generation and game not in FORMS_NAMED_BY_THE_GAME
        )


def generation_of(url: str) -> int:
    """The number in a generation's address, which is the only place the source writes it.

    The name is a roman numeral - ``generation-v`` - and the url ends in ``/generation/5/``.
    Reading the number is less work than agreeing with the wiki about numerals.
    """
    return int(url.rstrip("/").rsplit("/", 1)[-1])


class FormsError(Exception):
    """The form table could not be built. The message is meant for a human."""


@dataclass(frozen=True)
class FormTable:
    """The table the dataset carries, and where each entry's picture might be.

    The pictures are not part of the table: a form's record says what it is and which games
    have it, and which file a sprite sheet keeps it in is the sprite step's business. They come
    back together because working them out twice would mean walking every species twice.
    """

    forms: list[Form]
    #: Form id -> the names to try under a sprite set's folder, best first.
    pictures: Mapping[str, tuple[str, ...]]


def targets_of(
    api: PokeApiClient,
    species: str,
    known_forms: set[str],
    *,
    refresh: bool = False,
) -> list[tuple[str, DexTarget]]:
    """Every Pokemon of this species worth asking about, and what each one is in the dex.

    An encounter, a gift and a static all hang off a Pokemon rather than a species, and a species
    can be several of them: Rattata is ``rattata`` and ``rattata-alola``, Oricorio is four.

    The default Pokemon is the species itself, which is how every game before Generation 7
    reads: a Deerling caught in Unova is a Deerling, whichever coat the season gave it. Anything
    else is a form, and only when the asking game's own table has it - the source knows a Dusk
    Lycanroc and Sun does not, and inventing a target for it would put a tile in the grid that
    nothing could ever fill.
    """
    found: list[tuple[str, DexTarget]] = []

    for pokemon, is_default in api.varieties(species, refresh=refresh):
        if is_default:
            found.append((pokemon, DexTarget(species=species)))
        elif pokemon in known_forms:
            found.append((pokemon, DexTarget(species=species, form=pokemon)))

    return found or [(species, DexTarget(species=species))]


def form_table(
    api: PokeApiClient,
    *,
    species: Sequence[Species],
    game_ids: Iterable[str],
    refresh: bool = False,
) -> FormTable:
    """Every form of every species given, in the games that have it.

    By form id, which is the order :meth:`~.emit.DatasetWriter.write_forms` writes them in and
    therefore the order :func:`~.emit.read_forms` hands them back. Sorted here so that the table
    a full build holds in memory and the table a single-game build reads off disk are the same
    list: a game writes its form records in the order it is given them, and for a while the same
    game built two ways produced the same records twice over in two different orders.
    """
    groups = VersionGroupGames(api, frozenset(game_ids), refresh=refresh)
    found: list[Form] = []
    pictures: dict[str, tuple[str, ...]] = {}

    for one in species:
        found.extend(_forms_of(api, one, groups, pictures, refresh=refresh))

    return FormTable(forms=sorted(found, key=lambda one: one.id), pictures=pictures)


def form_pictures(
    api: PokeApiClient,
    forms: Sequence[Form],
    *,
    refresh: bool = False,
) -> dict[str, tuple[str, ...]]:
    """Where each of these forms' pictures might be, worked out from the source again.

    For a build that did not make the table itself. The table is on disk with everything the
    dataset needs; which file a sprite sheet would keep each picture in is not part of it, and
    this is cheaper than rebuilding the table to find out - only the species that have a form
    are asked about, and every answer is already in the cache.
    """
    wanted = {one.species for one in forms}
    numbers = {one.species: one for one in forms}
    pictures: dict[str, tuple[str, ...]] = {}

    for species in sorted(wanted):
        raw = api.resource(f"pokemon-species/{species}", refresh=refresh)
        default = _default_pokemon(api, raw, refresh=refresh)

        for pokemon, slug, face in _faces(api, raw, refresh=refresh):
            pictures[slug] = _pictures(face, pokemon, default=default)

        # The gender flag has no form anywhere in the source, so nothing above named it.
        pictures.setdefault(f"{species}-female", (f"female/{int(raw['id'])}.png",))

    # Only the forms actually asked about, so a species' unused faces do not leak in.
    return {one.id: pictures[one.id] for one in forms if one.id in pictures and numbers}


def _faces(api: PokeApiClient, raw: dict, *, refresh: bool):
    """Every face of a species, as (its Pokemon, the face's slug, the face).

    The walk both readings of the source need: varieties first, then the forms under each one,
    which is how a Wash Rotom and an Unown letter come out of the same loop.
    """
    for variety in raw["varieties"]:
        pokemon = api.resource(f"pokemon/{variety['pokemon']['name']}", refresh=refresh)

        for entry in pokemon["forms"]:
            yield (
                pokemon,
                entry["name"],
                api.resource(f"pokemon-form/{entry['name']}", refresh=refresh),
            )


def _forms_of(
    api: PokeApiClient,
    species: Species,
    groups: VersionGroupGames,
    pictures: dict[str, tuple[str, ...]],
    *,
    refresh: bool,
) -> list[Form]:
    raw = api.resource(f"pokemon-species/{species.id}", refresh=refresh)
    generation = generation_of(raw["generation"]["url"])

    # Asked before its varieties are, which saves the build a thousand requests: the species
    # table reaches every generation and this dataset stops at Generation 5, so most of what
    # would be fetched here is a Mega or a regional form of something no game has.
    if generation > groups.newest_generation:
        return []

    default = _default_pokemon(api, raw, refresh=refresh)

    found: list[Form] = []
    for pokemon, slug, face in _faces(api, raw, refresh=refresh):
        form = _form(
            species=species,
            pokemon=pokemon,
            default=default,
            slug=slug,
            face=face,
            groups=groups,
            generation=generation,
            pictures=pictures,
        )
        if form is not None:
            found.append(form)

    if raw.get("has_gender_differences") and not any(one.kind is FormKind.GENDER for one in found):
        gendered = _gender_form(species, groups, generation=generation)
        # Empty for a species from a generation this dataset does not reach yet, which is most
        # of them: Pyroar's sexes look nothing alike and no game here has a Pyroar.
        if gendered.games:
            found.append(gendered)
            # The one sprite layout that is a folder rather than a file name: a sheet keeps its
            # female sprites under `female/`, by the species' own number.
            pictures[gendered.id] = (f"female/{species.national_dex_number}.png",)

    return found


def _form(
    *,
    species: Species,
    pokemon: dict,
    default: dict,
    slug: str,
    face: dict,
    groups: VersionGroupGames,
    generation: int,
    pictures: dict[str, tuple[str, ...]],
) -> Form | None:
    raw = face

    # The species' own face, which is the line the form sits under rather than a form of it.
    if raw["is_default"] and pokemon["name"] == default["name"]:
        return None

    if (
        raw["is_battle_only"]
        or raw["is_mega"]
        or species.id in HELD_ITEM_FORMS
        or species.id in INVISIBLE_FORMS
    ):
        return None

    group = raw["version_group"]["name"]
    if not groups.knows(group):
        raise FormsError(f"{slug} names a version group nothing knows: {group}")

    games = [
        *(ONLY_IN.get(slug) or groups.from_group_on(group, generation=generation)),
        *groups.named_by_hand(slug),
    ]
    if not games:
        # Introduced after the last game this dataset holds, which every Mega, Gmax and
        # regional form of these species is. Expected rather than exceptional.
        return None

    pictures[slug] = _pictures(raw, pokemon, default=default)
    types = _types(raw, pokemon)

    return Form(
        id=slug,
        species=species.id,
        name=_label(raw["form_name"]),
        kind=_kind(raw["form_name"], pokemon=pokemon, default=default, types=types),
        games=sorted(games),
        types=types if types != species.types else None,
    )


def _pictures(raw: dict, pokemon: dict, *, default: dict) -> tuple[str, ...]:
    """Which file a sprite sheet would keep this form's picture in, best guess first.

    Two layouts, because a form is one of two things. A variety is its own Pokemon with its own
    number - Wash Rotom is 10009 - and a sheet files it under that. A face of one Pokemon has
    no number of its own and is filed under the species' number and the face's name, which is
    what the source's own address for it already says: ``585-summer.png``.

    Both are offered for a variety, because the sheets are not consistent about it: the
    spiky-eared Pichu is a variety and the Generation 4 sheet has it as ``172-spiky-eared.png``.
    The sprite step tries them in order and shrugs when a sheet has neither, which is the usual
    case - most sheets only drew what their own games showed.
    """
    named = _named_picture(raw)

    if pokemon["name"] != default["name"]:
        numbered = f"{pokemon['id']}.png"
        return (numbered, named) if named else (numbered,)

    return (named,) if named else ()


def _named_picture(raw: dict) -> str | None:
    """The file name the source's own address for this form ends in."""
    address = (raw.get("sprites") or {}).get("front_default")

    return address.rsplit("/", 1)[-1] if address else None


def _gender_form(species: Species, groups: VersionGroupGames, *, generation: int) -> Form:
    """The entry for a species whose sexes are drawn differently and have no form of their own.

    One line rather than two: the species' own line is the male, as the games' own sprite sets
    have it, and this is the other half.
    """
    return Form(
        id=f"{species.id}-female",
        species=species.id,
        name="Female",
        kind=FormKind.GENDER,
        games=sorted(
            [
                *groups.from_group_on(GENDER_FROM, generation=generation),
                *groups.named_by_hand(f"{species.id}-female"),
            ]
        ),
    )


def _kind(
    form_name: str,
    *,
    pokemon: dict,
    default: dict,
    types: list[PokemonType],
) -> FormKind:
    """Which switch decides whether this form is an entry.

    Measured rather than listed, and the measurement is the same question a player asks: is
    this a different Pokemon to raise, or the same one in different colours? Typing, base stats
    and abilities are what "different" means there, and a form that matches the species in all
    three is a repaint.
    """
    if form_name in REGIONAL:
        return FormKind.REGIONAL

    if form_name in GENDERED:
        return FormKind.GENDER

    if types != _types_of(default) or _stats(pokemon) != _stats(default):
        return FormKind.FUNCTIONAL

    if _abilities(pokemon) != _abilities(default):
        return FormKind.FUNCTIONAL

    return FormKind.COSMETIC


def _default_pokemon(api: PokeApiClient, raw: dict, *, refresh: bool) -> dict:
    name = next(variety["pokemon"]["name"] for variety in raw["varieties"] if variety["is_default"])

    return api.resource(f"pokemon/{name}", refresh=refresh)


def _types(raw: dict, pokemon: dict) -> list[PokemonType]:
    """The form's own typing when it carries one, the Pokemon's otherwise.

    The form carries it for every form that has one of its own, which is how Arceus's plates
    are told apart while sharing a single Pokemon between them.
    """
    if raw.get("types"):
        return _typed(raw["types"])

    return _types_of(pokemon)


def _types_of(pokemon: dict) -> list[PokemonType]:
    return _typed(pokemon["types"])


def _typed(entries: list[dict]) -> list[PokemonType]:
    return [PokemonType(one["type"]["name"]) for one in sorted(entries, key=_slot)]


def _slot(entry: dict) -> int:
    return int(entry["slot"])


def _stats(pokemon: dict) -> tuple[tuple[str, int], ...]:
    return tuple(
        (one["stat"]["name"], int(one["base_stat"]))
        for one in sorted(pokemon["stats"], key=lambda one: one["stat"]["name"])
    )


def _abilities(pokemon: dict) -> tuple[str, ...]:
    return tuple(sorted(one["ability"]["name"] for one in pokemon["abilities"]))


def _label(form_name: str) -> str:
    if form_name in LABELS:
        return LABELS[form_name]

    return "-".join(word.capitalize() for word in form_name.split("-"))
