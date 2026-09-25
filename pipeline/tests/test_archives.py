"""The pictures off the Archives: what they are called, and where the wiki keeps them."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import httpx
from PIL import Image

from livingdex_pipeline.archives import (
    ALOLA_SET,
    ARCHIVES,
    ARCHIVES_SHEETS,
    FORM_CODES,
    GALAR,
    GALAR_SET,
    HISUI,
    HOME,
    HOME_FORM_CODES,
    HOME_HAS_NO_PICTURE,
    HOME_SET,
    LETS_GO,
    LETS_GO_SET,
    SM,
    USUM,
    cropped,
    first_picture,
    form_names,
    media_url,
    species_names,
)
from livingdex_pipeline.build import Build
from livingdex_pipeline.emit import DatasetWriter
from livingdex_pipeline.models import (
    DexEntry,
    DexSource,
    DexTarget,
    Form,
    FormKind,
    Game,
    GameData,
    GameRelease,
    PokemonType,
    Species,
)


class Serving:
    """An Archives that holds exactly the files it was given, and 404s on everything else."""

    def __init__(self, *names: str) -> None:
        self.has = {media_url(name) for name in names}
        self.asked: list[str] = []

    def fetch(self, url: str, *, refresh: bool = False) -> object:
        self.asked.append(url)
        if url not in self.has:
            raise httpx.HTTPError("nothing here")

        class Entry:
            body = b"a picture"

        return Entry()


def species(*entries: tuple[int, str]) -> list[Species]:
    return [
        Species(
            id=name,
            national_dex_number=number,
            name=name.title(),
            types=[PokemonType.NORMAL],
            evolution_chain=name,
        )
        for number, name in entries
    ]


def alola_game(game_id: str = "sun", reach: int = 802) -> GameData:
    return GameData(
        game=Game(
            id=game_id,
            title=f"Pokemon {game_id.title()}",
            version=game_id.title(),
            released=date(2016, 11, 18),
            generation=7,
            region="Alola",
            release=GameRelease.CARTRIDGE,
            national_dex_through=reach,
            dex_source=DexSource.NATIONAL_DEX,
            sprite_set=ALOLA_SET,
        ),
        dex_entries=[DexEntry(game=game_id, target=DexTarget(species="rattata"), number=1)],
    )


# --- where a file lives -----------------------------------------------------------------------


def test_a_file_is_found_by_the_hash_of_its_name() -> None:
    # MediaWiki files an upload under the first digit of the MD5 of its name and the first two.
    # Reading the description page for the address, as a cover is, would double two thousand
    # requests against a host that asks five seconds between each.
    assert media_url("Spr_7s_019A.png") == f"{ARCHIVES}/media/upload/a/a1/Spr_7s_019A.png"
    assert media_url("Spr_7s_001.png") == f"{ARCHIVES}/media/upload/9/9a/Spr_7s_001.png"


# --- what a picture is called -----------------------------------------------------------------


def test_a_species_drawn_once_is_asked_for_plainly_first() -> None:
    assert species_names(1)[0] == "Spr_7s_001.png"


def test_a_species_drawn_twice_is_asked_for_as_the_male_first() -> None:
    # Rattata has no Spr_7s_019.png at all: where the sexes are drawn differently both files
    # carry a suffix and neither of them is the plain name.
    assert species_names(19, sexed=True)[0] == "Spr_7s_019_m.png"


def test_both_spellings_are_always_offered() -> None:
    # Being wrong about which comes first should cost one request, not a picture.
    assert set(species_names(19, sexed=True)) == set(species_names(19))


def test_the_number_is_always_three_digits() -> None:
    assert species_names(1)[0] == "Spr_7s_001.png"
    assert species_names(800)[0] == "Spr_7s_800.png"


def test_the_five_past_802_come_off_the_second_sheet() -> None:
    # Poipole, Naganadel, Stakataka, Blacephalon and Zeraora are what Ultra Sun and Ultra Moon
    # added, and Sun and Moon never drew them. Found by asking: every one of the 802 up to here
    # answered to 7s on the first name tried, and these five answered to nothing until 7u.
    assert species_names(802)[0] == "Spr_7s_802.png"
    assert species_names(803)[0] == "Spr_7u_803.png"
    assert species_names(807)[0] == "Spr_7u_807.png"


def test_a_species_whose_sexes_this_sheet_does_not_draw_still_gets_a_picture() -> None:
    # PokeAPI records a female Eevee and the Generation 7 sheet draws one Eevee. Offering both
    # spellings is what turns that disagreement into one wasted request instead of a hole.
    names = species_names(133, sexed=True)

    assert first_picture(Serving("Spr_7s_133.png"), names) == b"a picture"


def test_a_female_form_is_the_other_half_of_its_species() -> None:
    assert form_names(19, form_id="rattata-female", form_name="Female") == ("Spr_7s_019_f.png",)


def test_a_regional_form_takes_a_letter() -> None:
    assert form_names(19, form_id="rattata-alola", form_name="Alola")[0] == "Spr_7s_019A.png"


def test_a_form_with_no_code_is_not_asked_for_at_all() -> None:
    # A Totem Pokemon is drawn as the ordinary form and has no file of its own, which was
    # checked on the wiki rather than assumed. It falls back to the shared set's picture.
    assert form_names(752, form_id="araquanid-totem", form_name="Totem") == ()


def test_unowns_letters_turned_out_to_be_a_rule_after_all() -> None:
    # This module said for three generations that they are a hundred and thirty codes nobody has
    # read, and put them with Vivillon's patterns. Reading a whole category rather than probing
    # one name at a time showed the rule: the code is the letter.
    assert form_names(201, form_id="unown-b", form_name="B") == ("Spr_7s_201B.png",)
    assert form_names(201, form_id="unown-b", form_name="B", sheet=HISUI) == (
        "Spr_8a_201B.png",
    )

    # And the two that are not letters, which is the only part of it that is a list.
    assert form_names(201, form_id="unown-exclamation", form_name="!", sheet=HISUI) == (
        "Spr_8a_201EX.png",
    )
    assert form_names(201, form_id="unown-question", form_name="?", sheet=HISUI) == (
        "Spr_8a_201QU.png",
    )


# --- the second sheet, which is four pictures ---------------------------------------------------


def test_what_ultra_sun_added_comes_off_its_own_sheet() -> None:
    assert form_names(800, form_id="necrozma-dusk", form_name="Dusk") == ("Spr_7u_800DM.png",)


def test_two_forms_called_dusk_are_not_the_same_picture() -> None:
    # Lycanroc's Dusk Form is D and Necrozma's Dusk Mane is DM, and this dataset calls both
    # "Dusk" - which is why that table is keyed by the form rather than by the form's name.
    assert form_names(745, form_id="lycanroc-dusk", form_name="Dusk") == ("Spr_7u_745D.png",)


def test_the_four_sheets_are_told_apart() -> None:
    # 7p is Let's Go and not Ultra Sun and Ultra Moon. Matching on the number alone would have
    # given Alola a sheet drawn from the wrong games, at ten times the size. 8s is Galar's, and
    # it was read off a description page for the same reason rather than guessed at.
    assert (SM, USUM, LETS_GO, GALAR) == ("7s", "7u", "7p", "8s")


# --- and the second folder, which is the same rules with the sheet said out loud -----------------


def test_lets_go_names_its_own_sheet_instead_of_letting_the_number_choose() -> None:
    # Alola's four cartridges split across two sheets at SM_THROUGH, so there the number picks
    # one. These two are one sheet from Bulbasaur to Melmetal - and Melmetal is 809, which is
    # past the split and would otherwise have been asked for on Ultra Sun's.
    assert species_names(1, sheet=LETS_GO)[0] == "Spr_7p_001.png"
    assert species_names(809, sheet=LETS_GO)[0] == "Spr_7p_809.png"
    assert species_names(809)[0] == "Spr_7u_809.png"


def test_a_form_code_is_the_same_code_on_either_sheet() -> None:
    # An Alolan Rattata is 019A wherever it is drawn, which is what makes one namer enough for
    # both folders - and the reason a search that trusts the number finds the wrong picture.
    assert form_names(19, form_id="rattata-alola", form_name="Alola", sheet=LETS_GO)[0] == (
        "Spr_7p_019A.png"
    )


def test_what_ultra_sun_added_is_not_read_onto_another_sheet() -> None:
    # USUM_FORMS is the four pictures those two added to Sun and Moon's sheet and says nothing
    # about any other, so naming a sheet skips it rather than asking 7u for a Let's Go picture.
    assert form_names(800, form_id="necrozma-dusk", form_name="Dusk") == ("Spr_7u_800DM.png",)
    assert form_names(800, form_id="necrozma-dusk", form_name="Dusk", sheet=LETS_GO) == ()


def test_the_three_folders_know_which_sheet_fills_them() -> None:
    assert ARCHIVES_SHEETS[LETS_GO_SET] == LETS_GO
    assert ARCHIVES_SHEETS[GALAR_SET] == GALAR
    # Alola's is the one that works it out from the number, and nothing else does.
    assert ARCHIVES_SHEETS[ALOLA_SET] is None
    assert len({ALOLA_SET, LETS_GO_SET, GALAR_SET}) == 3

    # And Galar's is the first folder in the dataset that is not a Generation 7 one.
    assert GALAR_SET.startswith("generation-viii/")


def test_galar_reads_the_same_rules_as_generation_7_under_a_different_prefix() -> None:
    # The whole of what changed for a new generation: the sheet's name. Three digits, the same
    # form codes, the same _m and _f, and a number that decides nothing because these two games
    # name their own sheet - Melmetal at 809 would otherwise have been asked for on Ultra Sun's.
    assert species_names(810, sheet=GALAR) == ("Spr_8s_810.png", "Spr_8s_810_m.png")
    assert species_names(25, sheet=GALAR, sexed=True)[0] == "Spr_8s_025_m.png"
    assert species_names(809, sheet=GALAR)[0] == "Spr_8s_809.png"

    # Checked on the wiki rather than assumed: the Galarian Meowth is 052G, which is the same
    # shape as the Alolan one's 052A on either Generation 7 sheet.
    assert form_names(52, form_id="meowth-galar", form_name="Galar", sheet=GALAR)[0] == (
        "Spr_8s_052G.png"
    )
    assert form_names(52, form_id="meowth-alola", form_name="Alola", sheet=GALAR)[0] == (
        "Spr_8s_052A.png"
    )


# --- asking for one ---------------------------------------------------------------------------


def test_the_first_name_that_answers_is_the_one_used() -> None:
    archives = Serving("Spr_7s_019_m.png")

    assert first_picture(archives, species_names(19, sexed=True)) == b"a picture"
    assert archives.asked == [media_url("Spr_7s_019_m.png")]


def test_a_miss_is_ordinary_and_the_next_name_is_tried() -> None:
    archives = Serving("Spr_7s_019_m.png")

    assert first_picture(archives, species_names(19)) == b"a picture"
    assert archives.asked == [media_url("Spr_7s_019.png"), media_url("Spr_7s_019_m.png")]


def test_nothing_at_all_is_not_an_error() -> None:
    assert first_picture(Serving(), species_names(19)) is None


# --- the padding that comes off ------------------------------------------------------------------


def padded(width: int, height: int, drawn: tuple[int, int, int, int]) -> bytes:
    """A transparent frame with something opaque inside it, as the Archives hand one over."""
    picture = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    picture.paste(Image.new("RGBA", (drawn[2] - drawn[0], drawn[3] - drawn[1]), "red"), drawn[:2])
    out = io.BytesIO()
    picture.save(out, format="PNG")

    return out.getvalue()


def test_the_empty_air_around_a_picture_comes_off() -> None:
    # The Archives put every Generation 7 Pokemon in the same 240 pixel frame at its true size
    # against the others, so a Pikachu is 60 pixels of drawing in four times that much nothing.
    # In a 56 pixel tile that is a Pikachu at fourteen beside a Kalos one at fifty-six.
    body = cropped(padded(240, 240, (90, 90, 150, 150)))

    assert Image.open(io.BytesIO(body)).size == (60, 60)


def test_a_wide_pokemon_keeps_its_shape() -> None:
    # Cropping is to the drawing, not to a square: a Wailord comes out wide, the way every
    # Generation 6 sprite in this dataset already is.
    body = cropped(padded(240, 240, (40, 100, 185, 179)))

    assert Image.open(io.BytesIO(body)).size == (145, 79)


def test_a_picture_of_nothing_is_handed_back_as_it_was() -> None:
    empty = padded(240, 240, (0, 0, 0, 0))

    assert cropped(empty) == empty


# --- and what the build makes of it -------------------------------------------------------------


def test_a_sheet_already_in_the_dataset_opens_no_client(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    writer.write_sprite(f"{ALOLA_SET}/rattata.png", b"drawn earlier")
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")
    build._forms = []

    written = build._fetch_archives_set(ALOLA_SET, [alola_game()], species((19, "rattata")), writer)

    assert written == [tmp_path / "sprites" / ALOLA_SET / "rattata.png"]
    # The Archives are the five-second host. A warm dataset must cost nothing, or nobody will
    # ever build this at all.
    assert not (tmp_path / "cache" / "http").exists()


def test_the_sheet_reaches_as_far_as_the_widest_game_sharing_it(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")
    build._forms = []
    table = species((19, "rattata"), (805, "stakataka"), (810, "grookey"))

    kept, outstanding = build._archives_names(
        ALOLA_SET,
        [alola_game("sun", reach=802), alola_game("ultra-sun", reach=807)],
        table,
        writer,
    )

    # Sun stops at 802 and Ultra Sun goes to 807 and they draw from the same folder, so taking
    # the first game's reach would leave the five Ultra Sun added undrawn.
    assert kept == []
    assert [name for name, _ in outstanding] == ["rattata", "stakataka"]


def test_which_spelling_to_try_first_comes_out_of_the_form_table(tmp_path: Path) -> None:
    writer = DatasetWriter(tmp_path)
    build = Build(dataset_root=tmp_path, cache_root=tmp_path / "cache")
    build._forms = [
        Form(
            id="rattata-female",
            species="rattata",
            name="Female",
            kind=FormKind.COSMETIC,
            games=["sun"],
        )
    ]

    _, outstanding = build._archives_names(
        ALOLA_SET, [alola_game()], species((19, "rattata")), writer
    )
    planned = dict(outstanding)

    # A species drawn differently by sex is exactly one this dataset holds a female form for,
    # so the table it already has says which of the two spellings to ask for first.
    assert planned["rattata"][0] == "Spr_7s_019_m.png"
    assert planned["rattata-female"] == ("Spr_7s_019_f.png",)


def test_home_spells_a_name_its_own_way_and_more_simply() -> None:
    # Four digits, no sheet code, and a plain name for every species. A sheet draws a species
    # with visible sexes as `_m` and `_f` and gives it no plain name at all; HOME marks only the
    # female, so the plain name is always right and there is no second spelling to try.
    assert species_names(1, sheet=HOME) == ("HOME0001.png",)
    assert species_names(3, sheet=HOME, sexed=True) == ("HOME0003.png",)
    assert form_names(3, form_id="venusaur-female", form_name="Female", sheet=HOME) == (
        "HOME0003_f.png",
    )

    # **And it spells a form the way a sheet does, which step 6 of Legends: Z-A read off the
    # category.** This used to assert the opposite - that HOME had no rule for a form and so no
    # name - and that was true for exactly as long as the games drawing from this set named no
    # forms between them.
    assert form_names(479, form_id="rotom-heat", form_name="Heat", sheet=HOME) == (
        "HOME0479O.png",
    )

    # O for the oven and L for the lawnmower, which only the files' own description pages say.
    # Guessing alphabetically would have put a washing machine on the microwave's tile.
    assert form_names(479, form_id="rotom-mow", form_name="Mow", sheet=HOME) == ("HOME0479L.png",)

    # Two letters where a sheet uses one, which is why this is a table of its own.
    assert form_names(711, form_id="gourgeist-super", form_name="Super", sheet=HOME) == (
        "HOME0711Su.png",
    )

    # And a form it still has no rule for is no name rather than a guess, which falls back to
    # the shared set's picture - the right Pokemon in another generation's style.
    assert form_names(869, form_id="alcremie-ruby-cream", form_name="Ruby Cream", sheet=HOME) == ()


def test_the_home_set_is_the_first_here_that_is_not_a_generations() -> None:
    # Named for what it is rather than filed under a generation, because four games in two of
    # them will share it: these are the games the Archives have no sheet for at all.
    assert HOME_SET == "home"
    assert ARCHIVES_SHEETS[HOME_SET] == HOME
    assert not HOME_SET.startswith("generation-")



def test_hisuis_sheet_offers_a_form_code_where_a_species_name_belongs() -> None:
    # Fifteen species are in Legends: Arceus only as their Hisuian form, so the sheet draws no
    # plain one: Spr_8a_058.png does not exist and Spr_8a_058H.png is the Growlithe that game
    # has. Falling back to the shared set would put a Kantonian Growlithe on a Hisui tile.
    assert species_names(58, sheet=HISUI) == (
        "Spr_8a_058.png",
        "Spr_8a_058_m.png",
        "Spr_8a_058H.png",
        "Spr_8a_058H_m.png",
        "Spr_8a_058W.png",
        "Spr_8a_058W_m.png",
        "Spr_8a_058_f.png",
    )

    # Last, so a species drawn both ways still gets the plain one. Vulpix has both, and the
    # Pokedex entry is the Kantonian one.
    assert species_names(37, sheet=HISUI)[0] == "Spr_8a_037.png"

    # Sneasel is drawn four times, which is why the sexed spelling of the Hisuian name is here.
    assert species_names(215, sheet=HISUI, sexed=True)[:4] == (
        "Spr_8a_215_m.png",
        "Spr_8a_215.png",
        "Spr_8a_215H_m.png",
        "Spr_8a_215H.png",
    )


def test_the_two_species_the_hisui_sheet_names_its_own_way() -> None:
    # Basculin has no plain 550 at all: the White-Striped one is the only Basculin in Hisui and
    # the only one that becomes a Basculegion, and the sheet spells it W rather than H because
    # it is a form of the same shape rather than a regional one.
    assert "Spr_8a_550W.png" in species_names(550, sheet=HISUI)

    # And Floatzel is drawn once, as a female. That is an upload the wiki is short of rather
    # than a Floatzel the game is short of, so it is asked for last and only ever used when
    # nothing else answers.
    assert species_names(419, sheet=HISUI)[-1] == "Spr_8a_419_f.png"


def test_no_other_sheet_grew_a_hisuian_name() -> None:
    # The extra two are this sheet's alone. Asking Alola's or Galar's for them would be two
    # requests per species against a host that wants five seconds between each.
    for sheet in (SM, USUM, LETS_GO, GALAR):
        assert len(species_names(58, sheet=sheet)) == 2

    assert species_names(58, sheet=HOME) == ("HOME0058.png",)



def test_home_spells_every_kind_of_form_legends_z_a_has() -> None:
    # Twenty-six codes for ninety forms, read off a category of 3,126 files. Three of them are
    # the sheets' own letters a fourth time.
    assert HOME_FORM_CODES["Alola"] == "A"
    assert HOME_FORM_CODES["Galar"] == "G"
    assert HOME_FORM_CODES["Hisui"] == "H"
    assert FORM_CODES["Alola"] == HOME_FORM_CODES["Alola"]

    # And the rest are HOME's own, including three that are two letters where a sheet uses one.
    assert form_names(710, form_id="pumpkaboo-large", form_name="Large", sheet=HOME) == (
        "HOME0710La.png",
    )
    assert form_names(931, form_id="squawkabilly-blue-plumage", form_name="Blue-Plumage",
                      sheet=HOME) == ("HOME0931B.png",)
    assert form_names(999, form_id="gimmighoul-roaming", form_name="Roaming", sheet=HOME) == (
        "HOME0999R.png",
    )


def test_the_same_letter_means_two_things_and_the_species_is_what_tells_them_apart() -> None:
    # L is the lawnmower on a Rotom and Low Key on a Toxtricity; W is the washing machine and
    # the White Flower and the White Plumage. The number in front of it is what separates them,
    # which is why this table is keyed by a form's name rather than by a letter.
    assert HOME_FORM_CODES["Mow"] == HOME_FORM_CODES["Low-Key"] == "L"
    assert HOME_FORM_CODES["Wash"] == HOME_FORM_CODES["White"] == "W"

    assert form_names(479, form_id="rotom-mow", form_name="Mow", sheet=HOME) == ("HOME0479L.png",)
    assert form_names(849, form_id="toxtricity-low-key", form_name="Low-Key", sheet=HOME) == (
        "HOME0849L.png",
    )


def test_one_form_of_the_ninety_has_no_picture_and_it_is_not_the_one_the_category_said() -> None:
    # The finding worth keeping: reading the category said the Small Size Pumpkaboo was missing,
    # and asking for it got a picture. A category is a good index and not a complete one.
    assert HOME_HAS_NO_PICTURE == ("torchic-female",)
