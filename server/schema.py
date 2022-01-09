import graphene, requests, time

web_cache = {}


def resolve_site(url):
    if url in web_cache:
        if time.time() - web_cache[url]["time"] < 120:
            return web_cache[url]["data"]
    response = requests.get(url)
    web_cache[url] = {"time": time.time(), "data": response.json()}
    return response.json()


class BazaarInfo(graphene.ObjectType):
    buy_price = graphene.Float()
    sell_price = graphene.Float()


class Item(graphene.ObjectType):
    name = graphene.String()
    item_id = graphene.String()
    bazaar_info = graphene.Field(BazaarInfo)
    npc_sell_price = graphene.Float()

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
