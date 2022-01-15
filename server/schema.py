"""GraphQL schema."""
import gzip
import os
import re
import time

import graphene
import requests
import ujson

data_cache = {}

if not os.path.exists("neu_cache"):
    os.system(
        "git clone https://github.com/NotEnoughUpdates/NotEnoughUpdates-REPO neu_cache --depth 1"
    )


def resolve_json(resp):
    """Resolve JSON from a response (default utility function).

    Args:
        resp: The response object from requests.

    Returns:
        The parsed response of the site.
    """
    return resp.json()


def resolve_site(url, resolve=resolve_json, expiry=300):
    """Resolve a site using a cache.

    Args:
        url: The URL to resolve.
        resolve: A function to resolve the URL.
        expiry: The time in seconds to cache the response.

    Returns:
        The content of the URL.
    """
    cache_update_time = data_cache.get(url, {}).get("time") or 0
    if time.time() - cache_update_time > expiry:
        url_contents = resolve(requests.get(url))
        data_cache[url] = {"time": time.time(), "data": url_contents}
    return data_cache[url]["data"]


class BazaarInfo(graphene.ObjectType):
    """Object to store bazaar info for a Skyblock item."""

    buy_price = graphene.Float(description="The lowest buy price.")
    sell_price = graphene.Float(description="The highest sell price.")
    raw_data = graphene.String(description="Raw data from the Hypixel bazaar.")


class AuctionInfo(graphene.ObjectType):
    """Object to store auction info for a Skyblock item."""

    buy_price = graphene.Float(description="The lowest buy price.")
    sold_per_day = graphene.Int(description="The number sold per day.")
    raw_data = graphene.String(description="Raw data from the NEU auction house.")


class NEUInfo(graphene.ObjectType):
    """Object to store data from NotEnoughUpdates for a Skyblock item."""

    recipe = graphene.List(
        graphene.String,
        description="""The recipe for the Skyblock item. It's returned in the format of
[
    "ID:AMOUNT", "ID:AMOUNT", "ID:AMOUNT",
    "ID:AMOUNT", "ID:AMOUNT", "ID:AMOUNT",
    "ID:AMOUNT", "ID:AMOUNT", "ID:AMOUNT"
]""",
    )
    # TODO: Make the recipe return a list of objects instead of a list of strings.
    wiki_link = graphene.String(
        description="The Hypixel Skyblock fandom link for the Skyblock item."
    )
    raw_data = graphene.String(description="Raw data from the NEU database.")


BAZAAR_EXPIRY_SECONDS = 90


class SBItem(graphene.ObjectType):
    """Object to store data for a Skyblock item."""

    name = graphene.String(description="The plain name of the item.")
    item_id = graphene.String(description="The Skyblock ID of the item.")
    npc_sell_price = graphene.Float(description="The NPC sell price for the item.")
    raw_data = graphene.String(description="Raw data from the Hypixel items API.")
    bazaar_info = graphene.Field(
        BazaarInfo, description="Data from the Hypixel bazaar API."
    )
    auction_info = graphene.Field(
        AuctionInfo, description="Data from the NEU auction house."
    )
    neu_info = graphene.Field(NEUInfo, description="Data from the NEU database.")

    def resolve_bazaar_info(self, _execution_info):
        """Resolve an BazaarInfo for a Skyblock item.

        Returns:
            Data for a BazaarInfo object.
        """
        bz_products = resolve_site(
            "https://api.hypixel.net/skyblock/bazaar", expiry=BAZAAR_EXPIRY_SECONDS
        )["products"]
        return bz_products.get(self.item_id, {}).get("sell_summary") and {
            "buy_price": bz_products[self.item_id]["sell_summary"][0]["pricePerUnit"],
            "sell_price": bz_products[self.item_id]["buy_summary"][0]["pricePerUnit"],
            "raw_data": ujson.dumps(bz_products[self.item_id]),
        }

    def resolve_auction_info(self, _execution_info):
        """Resolve an AuctionInfo for a Skyblock item.

        Returns:
            Data for an AuctionInfo object.
        """
        auction_info = resolve_site(
            "https://moulberry.codes/auction_averages/3day.json.gz",
            resolve=lambda resp: ujson.loads(gzip.decompress(resp.content).decode()),
        )
        return self.item_id in auction_info and {
            "buy_price": auction_info[self.item_id]["price"],
            "sold_per_day": auction_info[self.item_id]["sales"],
            "raw_data": ujson.dumps(auction_info[self.item_id]),
        }

    def resolve_neu_info(self, _execution_info):
        """Resolve a NEUInfo for a Skyblock item.

        Returns:
            Data for a NEUInfo object.
        """
        item_path = f"neu_cache/items/{self.item_id}.json"
        if os.path.exists(item_path):
            with open(item_path) as item_file:
                item_data = ujson.load(item_file)
                return {
                    "recipe": item_data.get("recipe") and item_data["recipe"].values(),
                    "wiki_link": item_data.get("info") and item_data["info"][0],
                    "raw_data": ujson.dumps(item_data),
                }


class Query(graphene.ObjectType):
    """Base query for the schema."""

    sb_items = graphene.List(
        SBItem,
        name=graphene.String(),
        item_id=graphene.String(),
        description="Returns a list of [sb_items](https://api.hypixel.net/resources/skyblock/items). Filterable by name and item_id.",
    )

    def resolve_sb_items(self, _execution_info, name=None, item_id=None):
        """Resolve a list of Skyblock items.

        Args:
            name: The name of the item to filter by.
            item_id: The item ID to filter by.

        Returns:
            A list of items.
        """
        available_items = [
            SBItem(
                name=re.sub("§.", "", sb_item["name"]),
                item_id=sb_item["id"],
                npc_sell_price=sb_item.get("npc_sell_price"),
                raw_data=ujson.dumps(sb_item),
            )
            for sb_item in resolve_site(
                "https://api.hypixel.net/resources/skyblock/items"
            )["items"]
        ]
        if name:
            return [sb_item for sb_item in available_items if sb_item.name == name]
        elif item_id:
            return [
                sb_item for sb_item in available_items if sb_item.item_id == item_id
            ]
        return available_items


schema = graphene.Schema(query=Query)
