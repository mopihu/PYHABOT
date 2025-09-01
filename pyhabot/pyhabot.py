import asyncio
import aiohttp
import logging
import os
import sys
import random
from urllib.robotparser import RobotFileParser

from .config_handler import ConfigHandler
from .database_handler import DatabaseHandler
from .integrations.integration_base import IntegrationBase, MessageBase
from .command_handler import CommandHandler, COMMANDS
from .scraper import scrape_ads, get_url_params


logger = logging.getLogger("pyhabot_logger")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class Pyhabot:
    def __init__(self, integration: IntegrationBase):
        self.task: asyncio.Task | None = None
        self.chat_integration: IntegrationBase = integration
        persistent_data_path = os.getenv("PERSISTENT_DATA_PATH", "./persistent_data")
        self.config = ConfigHandler(persistent_data_path)
        self.db = DatabaseHandler(persistent_data_path)
        self.command = CommandHandler()
        self.session = None  # Will be created in _on_ready

        # Check robots.txt
        self._check_robots_txt()

        for cmd in COMMANDS:
            self.command.register_callback(cmd, getattr(self, f"_handle_{cmd["command"]}"))

        self.chat_integration.register_on_message_callback(self._on_message)
        self.chat_integration.register_on_ready_callback(self._on_ready)
        self.chat_integration.run()

    def _check_robots_txt(self):
        try:
            rp = RobotFileParser()
            rp.set_url("https://hardverapro.hu/robots.txt")
            rp.read()
            for ua in self.config.user_agents[:3]:  # Check first 3 user-agents
                if not rp.can_fetch(ua, "/"):
                    logger.warning(f"Robots.txt disallows scraping for user-agent: {ua}")
                else:
                    logger.info(f"Robots.txt allows scraping for user-agent: {ua}")
            if not rp.can_fetch("*", "/"):
                logger.warning("Robots.txt disallows scraping for all user-agents")
        except Exception as e:
            logger.warning(f"Failed to check robots.txt: {e}")

    async def _on_message(self, message: MessageBase):
        try:
            func = self.command.handle(message.text.split())
        except ValueError as err:
            await message.send_back(err.args[0])
            return
        if func is not None:
            await func(message)

    async def _on_ready(self):
        # Create aiohttp session now that we have an event loop
        if self.session is None:
            self.session = aiohttp.ClientSession()
        self.task = asyncio.get_event_loop().create_task(self.run_forever())

    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def run_forever(self):
        tries = 0
        while True:
            try:
                # Add jitter to refresh interval
                jitter = random.uniform(-self.config.interval_jitter_percent / 100, self.config.interval_jitter_percent / 100)
                jittered_interval = int(self.config.refresh_interval * (1 + jitter))
                watches = self.db.check_needed_for_watches(jittered_interval)
                for watch in watches:
                    num_of_new_ads = await self.handle_new_ads(watch)
                    logger.info(f"Scraped watch with ID: {watch['id']}, found {num_of_new_ads} new ads.")
                    # Add random delay between watches
                    if len(watches) > 1:
                        delay = random.uniform(self.config.request_delay_min, self.config.request_delay_max)
                        await asyncio.sleep(delay)
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                if tries < self.config.max_retries:
                    tries += 1
                    delay = self.config.retry_base_delay * (2 ** (tries - 1)) + random.uniform(0, 5)
                    logger.error(
                        f"Failure while checking adverts. Retrying in {delay:.1f} seconds.",
                        exc_info=exc,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries reached. Skipping this cycle.")
                    tries = 0
            else:
                tries = 0
                await asyncio.sleep(10)

    async def handle_new_ads(self, watch) -> int:
        new_ads = await self._get_new_ads(watch)
        for ad in new_ads:
            await self._send_notification(watch, ad)
        return len(new_ads)

    async def _get_new_ads(self, watch):
        new_ads = []
        session = await self._get_session()
        user_agent = random.choice(self.config.user_agents) if self.config.user_agents else None
        ads = await scrape_ads(watch["url"], session, user_agent)
        for ad in ads:
            try:
                self.db.add_advertisement(ad, watch["id"])
                new_ads.append(ad)
            except ValueError:
                price_changed = self.db.update_advertisement(ad)
                if price_changed:
                    await self._send_price_change_alert(watch, ad)
        existing_ads = self.db.get_active_advertisements(watch["id"])
        for ad in existing_ads:
            if ad["id"] not in [ad["id"] for ad in ads]:
                self.db.set_advertisement_inactive(ad["id"])
        self.db.set_watch_lastchecked(watch["id"])
        return new_ads

    async def _send_price_change_alert(self, watch, ad):
        # Extract previous prices
        prev_prices = ad.get("prev_prices", [])
        if not prev_prices:
            logger.info(f"No previous price data for {ad['title']}. Skipping price change alert.")
            return

        current_price = ad["price"]
        last_price = prev_prices[-1] if prev_prices else None

        if last_price is None or current_price is None or current_price == last_price:
            logger.info(f"No significant price change for {ad['title']}. Skipping alert.")
            return

        # Construct alert message
        change_type = "increased" if current_price > last_price else "decreased"
        date_display = "Pinned" if ad.get('pinned') else ad['date']
        txt = f"**Árváltozás: [{ad['title']}]({ad['url']})**\n"
        txt += f"Új ár: {current_price} Ft ({change_type})\n\n"
        txt += f"Előző ár: {last_price} Ft\n"
        txt += f"**{ad['city']}** | {date_display} | {ad['seller_name']} ({ad['seller_rates']})\n"
        txt += f"![Image]({ad['image']})"

        # Send notification if configured
        notifyon = watch.get("notifyon")
        if notifyon:
            if self.chat_integration.name == notifyon["integration"]:
                await self.chat_integration.send_message_to_channel(notifyon["channel_id"], txt)
            else:
                logger.warning(
                    f"Tried to send price change alert to '{notifyon['integration']}', but bot is using {self.chat_integration.name}."
                )

        # Send webhook if configured
        if watch.get("webhook"):
            payload = {
                "username": "pyhabot",
                "avatar_url": "https://github.com/Patrick2562/PYHABOT/blob/master/assets/avatar.png",
                "content": txt,
            }
            session = await self._get_session()
            await session.post(watch["webhook"], json=payload)

        logger.info(f"Sent price change alert for {ad['title']} (was {last_price} Ft, now {current_price} Ft).")

    async def _send_notification(self, watch, ad):
        stext, minprice, maxprice = get_url_params(watch["url"])
        txt = f"**{stext}**\n"
        txt += f"{minprice} - {maxprice} Ft\n\n"
        date_display = "Pinned" if ad.get('pinned') else ad['date']
        txt += f"[{ad['title']}]({ad['url']})\n"
        txt += f"**{ad['price']}** ({ad['city']}) ({date_display}) ({ad['seller_name']} {ad['seller_rates']})"

        notifyon = watch["notifyon"]
        if notifyon is not None:
            if self.chat_integration.name == notifyon["integration"]:
                await self.chat_integration.send_message_to_channel(notifyon["channel_id"], txt)
            else:
                logger.warning(
                    f"Tried to send notification to '{notifyon['integration']}', but failed because bot started with {self.chat_integration.name} integration.'"
                )

        if watch["webhook"] is not None:
            payload = {
                "username": "pyhabot",
                "avatar_url": "https://github.com/Patrick2562/PYHABOT/blob/master/assets/avatar.png",
                "content": txt,
            }
            session = await self._get_session()
            await session.post(watch["webhook"], json=payload)

    async def _handle_help(self, msg: MessageBase):
        await msg.send_back(f"```\n{self.command.help()}```")

    async def _handle_settings(self, msg: MessageBase):
        text = f"- Integration: {self.chat_integration.name}\n"
        text += f"- Commands prefix: {self.config.commands_prefix}\n"
        text += f"- Refresh interval: {self.config.refresh_interval} sec"
        await msg.send_back(text)

    async def _handle_setprefix(self, msg: MessageBase, prefix):
        self.config.commands_prefix = prefix
        self.command.prefix = prefix
        await msg.send_back(f"Prefix módosítva: `{prefix}`")

    async def _handle_setinterval(self, msg: MessageBase, interval):
        self.config.refresh_interval = interval
        await msg.send_back(f"Refresh interval módosítva: `{interval} sec`")

    async def _handle_add(self, msg: MessageBase, url):
        watchid = self.db.add_watch(url)
        self.db.set_watch_notifyon(watchid, msg.channel_id, self.chat_integration.name)
        await self.handle_new_ads(self.db.get_watch(watchid))
        await msg.send_back(f"Sikeresen hozzáadva! - ID: `{watchid}`")

    async def _handle_remove(self, msg: MessageBase, watchid):
        try:
            self.db.remove_watch(watchid)
            await msg.send_back(f"Sikeresen törölve! - ID: `{watchid}`")
        except KeyError:
            await msg.send_back(f"ID: `{watchid}` nem létezik. Sikertelen törlés.")

    async def _handle_list(self, msg: MessageBase):
        txt = ""
        for doc in self.db.get_all_watch():
            txt += f"{'\n' if txt else ''}ID: `{doc["id"]}` - {msg.format_hyperlink(get_url_params(doc['url'])[0], doc['url'])}\n"
        await msg.send_back(txt if txt else "Nincs még felvett hirdetésfigyelő!", no_preview=True)

    async def _handle_info(self, msg: MessageBase, watchid):
        watch = self.db.get_watch(watchid)
        if watch is None:
            await msg.send_back(f"ID: `{watchid}` nem létezik.")
            return
        stext, minprice, maxprice = get_url_params(watch["url"])
        txt = f"ID: `{watchid}`\n"
        txt += f"Search text: {stext}\n"
        txt += f"Price limit: {minprice} - {maxprice} Ft\n"
        txt += f"Notify on: {watch['notifyon']['integration'] if watch['notifyon'] is not None else 'None'}\n"
        txt += f"Webhook: {'set' if watch['webhook'] is not None else 'None'}\n"
        txt += f"Number of active ads: {len(self.db.get_active_advertisements(watchid))} (all: {len(self.db.get_all_advertisements(watchid))})\n"
        txt += f"{msg.format_hyperlink('link', watch['url'])}n"
        await msg.send_back(txt, no_preview=True)

    async def _handle_seturl(self, msg: MessageBase, watchid, url):
        try:
            self.db.set_url(watchid, url)
            self.db.clear_advertisements(watchid)
            self.db.reset_watch_last_checked(watchid)
            await msg.send_back(f"URL módosítva! - ID: `{watchid}`")
        except KeyError:
            await msg.send_back(f"ID: `{watchid}` nem létezik. Sikertelen módosítás.")

    async def _handle_notifyon(self, msg: MessageBase, watchid):
        try:
            self.db.set_watch_notifyon(watchid, msg.channel_id, self.chat_integration.name)
            await msg.send_back(f"Értesítés beállítva! - ID: `{watchid}`")
        except KeyError:
            await msg.send_back(f"ID: `{watchid}` nem létezik. Sikertelen módosítás.")

    async def _handle_setwebhook(self, msg: MessageBase, watchid, url):
        try:
            self.db.set_watch_webhook(watchid, url)
            await msg.send_back(f"Webhook URL beállítva! - ID: `{watchid}`")
        except KeyError:
            await msg.send_back(f"ID: `{watchid}` nem létezik. Sikertelen módosítás.")

    async def _handle_unsetwebhook(self, msg: MessageBase, watchid):
        try:
            self.db.clear_watch_webhook(watchid)
            await msg.send_back(f"Webhook URL törölve! - ID: `{watchid}`")
        except KeyError:
            await msg.send_back(f"ID: `{watchid}` nem létezik. Sikertelen módosítás.")

    async def _handle_rescrape(self, msg: MessageBase, watchid):
        if watchid is None:
            self.db.clear_all_advertisements()
            self.db.reset_all_watch_last_checked()
            await msg.send_back(f"Összes hirdetés újbóli átvizsgálása...")
        else:
            watch = self.db.get_watch(watchid)
            if watch is None:
                await msg.send_back(f"ID: `{watchid}` nem létezik.")
                return
            self.db.clear_advertisements(watchid)
            self.db.reset_watch_last_checked(watchid)
            await self.handle_new_ads(watch)
            await msg.send_back(f"ID: `{watchid}` hirdetésújbóli átvizsgálása...")

    async def _handle_listads(self, msg: MessageBase, watchid):
        active_text = ""
        for ad in self.db.get_active_advertisements(watchid):
            active_text += f"ID: `{ad["id"]}` - {msg.format_hyperlink(ad['title'], ad['url'])} - {ad['price']} Ft\n"

        inactive_text = ""
        for ad in self.db.get_inactive_advertisements(watchid):
            inactive_text += f"ID: `{ad["id"]}` - {msg.format_hyperlink(ad['title'], ad['url'])} - {ad['price']} Ft\n"

        text = active_text + (("\nInaktív hirdetések:\n" + inactive_text) if inactive_text else "")

        if text:
            await msg.send_back(text, no_preview=True)
        else:
            await msg.send_back(
                f"ID: `{watchid}` vagy nem létezik a hirdetésfigyelő vagy nem tartoznak hozzá hirdetések."
            )

    async def _handle_adinfo(self, msg: MessageBase, adid):
        ad = self.db.get_advertisement(adid)
        if ad is None:
            await msg.send_back(f"ID: `{adid}` nem létezik.")
            return

        date_display = "Pinned" if ad.get('pinned') else ad['date']
        text = f"ID: `{ad['id']}`\n"
        text += f"Cím: {ad['title']}\n"
        text += f"Ár: {ad['price']} Ft\n"
        text += f"Város: {ad['city']}\n"
        text += f"Utolsó up: {date_display}\n"
        text += f"Feladó: {ad['seller_name']} ({ad['seller_rates']})\n"
        text += f"Watch ID: `{ad['watch_id']}`\n"
        text += f"Aktív: {"igen" if ad['active'] else "nem"}\n"
        text += f"Korábbi árai: {", ".join(ad['prev_prices'])}\n"
        text += f"{msg.format_hyperlink("link", ad['url'])}\n"
        await msg.send_back(text)

    async def _handle_setpricealert(self, msg: MessageBase, adid):
        if self.db.set_advertisement_price_alert(adid, True):
            await msg.send_back(f"Árváltozás követés beállítva! - ID: `{adid}`")
        else:
            await msg.send_back(f"ID: `{adid}` nem létezik. Sikertelen módosítás.")

    async def _handle_unsetpricealert(self, msg: MessageBase, adid):
        if self.db.set_advertisement_price_alert(adid, False):
            await msg.send_back(f"Árváltozás követés kikapcsolva! - ID: `{adid}`")
        else:
            await msg.send_back(f"ID: `{adid}` nem létezik. Sikertelen módosítás.")
