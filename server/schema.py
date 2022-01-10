"""GraphQL schema."""
import gzip
import os
import time

import graphene
import requests
import ujson

data_cache = {}

if not os.path.exists("neu_cache"):
    os.system(
        "git clone https://github.com/NotEnoughUpdates/NotEnoughUpdates-REPO neu_cache --depth 1"
    )


def resolve_site(url, resolve=lambda resp: resp.json(), expiry=300):
    """Resolve a site using a cache.

    Args:
        url: The URL to resolve.
        resolve: A function to resolve the URL.
        expiry: The time in seconds to cache the response.

    Returns:
        The content of the URL.
    """
    if url not in data_cache or time.time() - data_cache[url]["time"] > expiry:
        data_cache[url] = {"time": time.time(), "data": resolve(requests.get(url))}
    return data_cache[url]["data"]


class BazaarInfo(graphene.ObjectType):
    """Object to store bazaar info for an item."""

    buy_price = graphene.Float()
    sell_price = graphene.Float()
    raw_data = graphene.String()


class AuctionInfo(graphene.ObjectType):
    """Object to store auction info for an item."""

    buy_price = graphene.Float()
    sold_per_day = graphene.Int()
    raw_data = graphene.String()


class NEUInfo(graphene.ObjectType):
    """Object to store data from NotEnoughUpdates for an item."""

    recipe = graphene.List(graphene.String)
    wiki_link = graphene.String()
    raw_data = graphene.String()


class Item(graphene.ObjectType):
    """Object to store data for an item."""

    name = graphene.String()
    item_id = graphene.String()
    npc_sell_price = graphene.Float()
    raw_data = graphene.String()
    bazaar_info = graphene.Field(BazaarInfo)
    auction_info = graphene.Field(AuctionInfo)
    neu_info = graphene.Field(NEUInfo)

    def resolve_bazaar_info(self, _info):
        """Resolve an BazaarInfo for an item.

        Returns:
            Data for a BazaarInfo object.
        """
        bz_products = resolve_site(
            "https://api.hypixel.net/skyblock/bazaar", expiry=90
        )["products"]
        return bz_products.get(self.item_id, {}).get("sell_summary") and {
            "buy_price": bz_products[self.item_id]["buy_summary"][0]["pricePerUnit"],
            "sell_price": bz_products[self.item_id]["sell_summary"][0]["pricePerUnit"],
            "raw_data": ujson.dumps(bz_products[self.item_id]),
        }

    def resolve_auction_info(self, _info):
        """Resolve an AuctionInfo for an item.

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

    def resolve_neu_info(self, _info):
        """Resolve a NEUInfo for an item.

        Returns:
            Data for a NEUInfo object.
        """
        item_path = f"neu_cache/items/{self.item_id}.json"
        item_data = os.path.exists(item_path) and ujson.load(open(item_path))
        return item_data and {
            "recipe": item_data["recipe"].values() if "recipe" in item_data else None,
            "wiki_link": item_data["info"][0] if "info" in item_data else None,
            "raw_data": ujson.dumps(item_data),
        }


class Query(graphene.ObjectType):
    """Base query for the schema."""

    items = graphene.List(
        Item,
        name=graphene.String(),
        item_id=graphene.String(),
        description="""Returns a list of [items](https://api.hypixel.net/resources/skyblock/items).
Filterable by name and item_id.""",
    )

    def resolve_items(self, _info, name=None, item_id=None):
        """Resolve a list of items.

        Args:
            name: The name of the item to filter by.
            item_id: The item ID to filter by.

        Returns:
            A list of items.
        """
        available_items = [
            Item(
                name=item["name"],
                item_id=item["id"],
                npc_sell_price=item.get("npc_sell_price"),
                raw_data=ujson.dumps(item),
            )
            for item in resolve_site(
                "https://api.hypixel.net/resources/skyblock/items"
            )["items"]
        ]
        if name:
            return [item for item in available_items if item.name == name]
        elif item_id:
            return [item for item in available_items if item.item_id == item_id]
        return available_items


schema = graphene.Schema(query=Query)
