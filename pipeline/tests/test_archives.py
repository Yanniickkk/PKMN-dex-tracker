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
    GALAR,
    GALAR_SET,
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
    # checked on the wiki rather than assumed; Unown's letters have a hundred and thirty codes
    # nobody has read. Both fall back to the shared set's picture of that form.
    assert form_names(752, form_id="araquanid-totem", form_name="Totem") == ()
    assert form_names(201, form_id="unown-b", form_name="B") == ()


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
