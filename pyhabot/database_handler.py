from pathlib import Path
from tinydb import Query, TinyDB
from tinydb.table import Document
from datetime import datetime


WATCHLIST_FILENAME = "watchlist.json"


class DatabaseHandler:
    def __init__(self, folder: Path | str, filename: str = WATCHLIST_FILENAME):
        folder = Path(folder)
        folder.mkdir(exist_ok=True)
        self.db = TinyDB(folder / filename)
        self.watchlist = self.db.table("watchlist")
        self.advertisements = self.db.table("advertisements")

    def get_watch(self, id):
        return self.watchlist.get(doc_id=id)

    def get_all_watch(self):
        return [{**doc} for doc in self.watchlist]

    def add_watch(self, url):
        id_ = self.watchlist.insert({"url": url, "last_checked": 0.0, "notifyon": None, "webhook": None})
        self.watchlist.update({"id": id_}, doc_ids=[id_])
        return id_

    def reset_watch_last_checked(self, id_):
        self.watchlist.update({"last_checked": 0.0}, doc_ids=[id_])

    def reset_all_watch_last_checked(self):
        self.watchlist.update({"last_checked": 0.0})

    def remove_watch(self, id_):
        self.watchlist.remove(doc_ids=[id_])
        self.clear_advertisements(id_)

    def set_watch_url(self, id_, url):
        self.watchlist.update({"url": url}, doc_ids=[id_])

    def set_watch_notifyon(self, id_, channel_id, integration_name):
        self.watchlist.update(
            {"notifyon": {"channel_id": channel_id, "integration": integration_name}},
            doc_ids=[id_],
        )

    def set_watch_lastchecked(self, id_):
        self.watchlist.update({"last_checked": datetime.now().timestamp()}, doc_ids=[id_])

    def check_needed_for_watches(self, check_interval):
        Watch = Query()
        threshold = int(datetime.now().timestamp()) - check_interval  # Convert to int
        return self.watchlist.search(Watch.last_checked < threshold)

    def clear_watch_notifyon(self, id_):
        self.watchlist.update({"notifyon_channel_id": None}, doc_ids=[id_])

    def set_watch_webhook(self, id_, webhook):
        self.watchlist.update({"webhook": webhook}, doc_ids=[id_])

    def clear_watch_webhook(self, id_):
        self.watchlist.update({"webhook": None}, doc_ids=[id_])

    def get_advertisement(self, id_):
        return self.advertisements.get(doc_id=id_)

    def add_advertisement(self, data, watch_id):
        return self.advertisements.insert(
            Document(
                {**data, "prev_prices": [], "watch_id": watch_id, "active": True, "price_alert": False},
                doc_id=data["id"],
            )
        )

    def update_advertisement(self, data):
        self.advertisements.update({"active": True}, doc_ids=[data["id"]])  # in case it was inactive
        doc = self.advertisements.get(doc_id=data["id"])
        if doc is not None and doc["price"] != data["price"]:
            self.advertisements.update(
                {"prev_prices": doc["prev_prices"] + [doc["price"]]},
                doc_ids=[data["id"]],
            )
            self.advertisements.update({"price": data["price"]}, doc_ids=[data["id"]])
            return True
        return False

    def set_advertisement_price_alert(self, id_, value: bool):
        try:
            self.advertisements.update({"price_alert": value}, doc_ids=[id_])
            return True
        except KeyError:
            return False

    def remove_advertisement(self, id_):
        self.advertisements.remove(doc_ids=[id_])

    def set_advertisement_inactive(self, id_):
        self.advertisements.update({"active": False}, doc_ids=[id_])

    def get_active_advertisements(self, watch_id):
        Ad = Query()
        return self.advertisements.search((Ad.watch_id == watch_id) & (Ad.active == True))

    def get_inactive_advertisements(self, watch_id):
        Ad = Query()
        return self.advertisements.search((Ad.watch_id == watch_id) & (Ad.active == False))

    def get_all_advertisements(self, watch_id):
        Ad = Query()
        return self.advertisements.search(Ad.watch_id == watch_id)

    def clear_advertisements(self, watch_id):
        Ad = Query()
        self.advertisements.remove(Ad.watch_id == watch_id)

    def clear_all_advertisements(self):
        self.advertisements.truncate()


if __name__ == "__main__":
    db = DatabaseHandler("./persistent_data")
    db.add_advertisement({"id": "test", "title": "Test", "price": 100}, 1)
