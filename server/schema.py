import graphene, requests, time
import ujson, gzip

web_cache = {}


def resolve_site(url, resolve=lambda resp: resp.json()):
    if url in web_cache:
        if time.time() - web_cache[url]["time"] < 120:
            return web_cache[url]["data"]
    response = requests.get(url)
    web_cache[url] = {"time": time.time(), "data": resolve(response)}
    return resolve(response)


class BazaarInfo(graphene.ObjectType):
    buy_price = graphene.Float()
    sell_price = graphene.Float()


class AuctionInfo(graphene.ObjectType):
    buy_price = graphene.Float()
    sold_per_day = graphene.Int()


class Item(graphene.ObjectType):
    name = graphene.String()
    item_id = graphene.String()
    npc_sell_price = graphene.Float()
    bazaar_info = graphene.Field(BazaarInfo)
    auction_info = graphene.Field(AuctionInfo)

    def resolve_bazaar_info(self, _info):
        bz_products = resolve_site("https://api.hypixel.net/skyblock/bazaar")["products"]
        return (
            {
                "buy_price": bz_products[self.item_id]["sell_summary"][0]["pricePerUnit"],
                "sell_price": bz_products[self.item_id]["buy_summary"][0]["pricePerUnit"],
            }
            if self.item_id in bz_products and bz_products[self.item_id]["sell_summary"]
            else None
        )

    def resolve_auction_info(self, _info):
        auction_info = resolve_site(
            "https://moulberry.codes/auction_averages/3day.json.gz",
            resolve=lambda resp: ujson.loads(gzip.decompress(resp.content).decode()),
        )
        return (
            {"buy_price": auction_info[self.item_id]["price"], "sold_per_day": auction_info[self.item_id]["sales"]}
            if self.item_id in auction_info
            else None
        )


class Query(graphene.ObjectType):
    items = graphene.List(Item, name=graphene.String(), item_id=graphene.String())

    def resolve_items(self, info, name=None, item_id=None):
        available_items = [
            Item(
                name=item["name"],
                item_id=item["id"],
                npc_sell_price=item.get("npc_sell_price"),
            )
            for item in resolve_site("https://api.hypixel.net/resources/skyblock/items")["items"]
        ]
        if name:
            return [item for item in available_items if item.name == name]
        elif item_id:
            return [item for item in available_items if item.item_id == item_id]
        else:
            return available_items


schema = graphene.Schema(query=Query)
