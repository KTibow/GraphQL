import graphene, requests, time

all_items = requests.get("https://api.hypixel.net/resources/skyblock/items")
all_items = all_items.json()["items"]

bazaar_info = requests.get("https://api.hypixel.net/skyblock/bazaar")
bazaar_info = bazaar_info.json()["products"]
last_bazaar_update = time.time()


class BazaarInfo(graphene.ObjectType):
    buy_price = graphene.Float()
    sell_price = graphene.Float()


class Item(graphene.ObjectType):
    name = graphene.String()
    item_id = graphene.String()
    bazaar_info = graphene.Field(BazaarInfo)
    npc_sell_price = graphene.Float()

    def resolve_bazaar_info(self, info):
        global bazaar_info, last_bazaar_update
        if time.time() - last_bazaar_update > 120:
            bazaar_info = requests.get("https://api.hypixel.net/skyblock/bazaar")
            bazaar_info = bazaar_info.json()["products"]
            last_bazaar_update = time.time()
        
        if self.item_id in bazaar_info and len(bazaar_info[self.item_id]["sell_summary"]) > 0:
            highest_buy_price = bazaar_info[self.item_id]["sell_summary"][0]["pricePerUnit"]
            lowest_sell_price = bazaar_info[self.item_id]["buy_summary"][0]["pricePerUnit"]
            return BazaarInfo(buy_price=lowest_sell_price, sell_price=highest_buy_price)
        else:
            return None


class Query(graphene.ObjectType):
    items = graphene.List(Item, name=graphene.String(), item_id=graphene.String())

    def resolve_items(self, info, name=None, item_id=None):
        available_items = [
            Item(
                name=item["name"],
                item_id=item["id"],
                npc_sell_price=item.get("npc_sell_price"),
            )
            for item in all_items
        ]
        if name:
            return [item for item in available_items if item.name == name]
        elif item_id:
            return [item for item in available_items if item.item_id == item_id]
        else:
            return available_items


schema = graphene.Schema(query=Query)
