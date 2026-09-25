"""A thin PokeAPI client.

PokeAPI is the spine of the dataset: it supplies species, National Dex numbers, types,
evolution chains and sprites, and its ids are what everything scraped elsewhere gets matched
onto. It is deliberately not asked for encounter data — that is what the scrapers are for,
because per-game encounter detail is where PokeAPI is thinnest.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from .http import PoliteClient
from .models import PokemonType, Species

BASE_URL = "https://pokeapi.co/api/v2"


class PokeApiClient:
    def __init__(self, client: PoliteClient, base_url: str = BASE_URL) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    def resource(self, path: str, *, refresh: bool = False) -> Any:
        return self._client.get_json(f"{self._base_url}/{path.lstrip('/')}", refresh=refresh)

    def retrieved_on(self, url: str) -> date:
        """When the answer at this url was fetched.

        Takes the whole url rather than a path, because it answers for the citation a caller
        is already building and that is what a citation carries.
        """
        return self._client.retrieved_on(url)

    def newest_read_under(self, url: str) -> date:
        """When the most recently read thing under this url was fetched.

        For a citation that names a collection rather than one of its pages, which is a url
        nobody fetches: the answer it stands for was read chain by chain.
        """
        return self._client.newest_read_under(url)

    def species_list(self, *, limit: int = 2000, refresh: bool = False) -> list[dict[str, Any]]:
        """Every species, name and url, in National Dex order."""
        page = self.resource(f"pokemon-species?limit={limit}", refresh=refresh)
        return list(page.get("results", []))

    def species(self, name: str, *, refresh: bool = False) -> Species:
        """One species, as the dataset models it."""
        raw = self.resource(f"pokemon-species/{name}", refresh=refresh)
        default_variety = self._default_variety(raw, refresh=refresh)

        return Species(
            id=raw["name"],
            national_dex_number=raw["id"],
            name=self._display_name(raw),
            types=[PokemonType(entry["type"]["name"]) for entry in default_variety["types"]],
            evolution_chain=self._evolution_chain_id(raw),
        )

    def pokedex(self, name: str, *, refresh: bool = False) -> list[tuple[int, str]]:
        """One regional dex as (number in that dex, species name), in its own order.

        PokeAPI keeps the regional dexes as their games list them, which is exactly what a game
        file needs: Hoenn starts at Treecko, not at Bulbasaur.
        """
        raw = self.resource(f"pokedex/{name}", refresh=refresh)

        return sorted(
            (entry["entry_number"], entry["pokemon_species"]["name"])
            for entry in raw.get("pokemon_entries", [])
        )

    def default_pokemon(self, species: str, *, refresh: bool = False) -> str:
        """The name of a species' default form.

        Encounters hang off a Pokemon, not a species, and for anything with forms the two are
        spelled differently: the species is ``deoxys``, the Pokemon is ``deoxys-normal``, and
        asking for the species by name is a 404.
        """
        raw = self.resource(f"pokemon-species/{species}", refresh=refresh)
        default = next((one for one in raw.get("varieties", []) if one.get("is_default")), None)

        return default["pokemon"]["name"] if default else species

    def varieties(self, species: str, *, refresh: bool = False) -> list[tuple[str, bool]]:
        """Every Pokemon this species has, and which of them is the default one.

        The same resource :meth:`default_pokemon` reads, asked the whole question. A species can
        be more than one Pokemon in the source - Rattata is ``rattata`` and ``rattata-alola``,
        Oricorio is four - and each of them carries its own encounter table. Asking only for the
        default is what leaves a game whose grass holds nothing but the regional form with no
        answer at all to "where do I catch one".
        """
        raw = self.resource(f"pokemon-species/{species}", refresh=refresh)

        return [
            (one["pokemon"]["name"], bool(one.get("is_default")))
            for one in raw.get("varieties", [])
        ]

    def evolution_chain(self, species: str, *, refresh: bool = False) -> str:
        """The id of the chain a species belongs to.

        Chains are shared by everything in them, so this is also how a list of species becomes
        the much shorter list of chains worth fetching.
        """
        raw = self.resource(f"pokemon-species/{species}", refresh=refresh)
        return self._evolution_chain_id(raw)

    def encounters(self, pokemon: str, *, refresh: bool = False) -> list[Any]:
        """Where one Pokemon is met in the wild, per version, as PokeAPI records it.

        This is the games' own encounter table, which is why it is asked for here rather than
        scraped: area, method, level range and slot chance, already structured.
        """
        return self.resource(f"pokemon/{pokemon}/encounters", refresh=refresh)

    def sprite_url(self, species_id: int, sprite_set: str | None = None) -> str:
        """The front-facing sprite for a species, by National Dex number.

        Without a set this is the current artwork, which is what the app falls back to. With
        one it is that set's own sprite - ``generation-iii/emerald`` gives the 64x64 battle
        sprite an Emerald player actually saw, which is the point of Phase 2 step 6.
        """
        where = f"versions/{sprite_set}/" if sprite_set else ""

        return (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
            f"{where}{species_id}.png"
        )

    def _default_variety(self, raw: dict[str, Any], *, refresh: bool) -> dict[str, Any]:
        """Types live on the Pokemon, not the species, so the default variety is fetched."""
        varieties = raw.get("varieties", [])
        default = next((one for one in varieties if one.get("is_default")), None)
        if default is None:
            return {"types": []}

        return self._client.get_json(default["pokemon"]["url"], refresh=refresh)

    @staticmethod
    def _display_name(raw: dict[str, Any]) -> str:
        for entry in raw.get("names", []):
            if entry.get("language", {}).get("name") == "en":
                return entry["name"]

        # Fall back to the slug rather than failing: a missing English name is a gap in the
        # source, not a reason to abandon a build.
        return str(raw["name"]).replace("-", " ").title()

    @staticmethod
    def _evolution_chain_id(raw: dict[str, Any]) -> str:
        chain = raw.get("evolution_chain")
        if not chain:
            # A species with no chain is its own chain, which keeps the field non-null.
            return str(raw["name"])

        return chain["url"].rstrip("/").rsplit("/", 1)[-1]
