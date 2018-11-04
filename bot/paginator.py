import asyncio
import logging
import math
import time

from .discord import EventType

EMOJI_PREV = '\N{BLACK LEFT-POINTING TRIANGLE}'
EMOJI_NEXT = '\N{BLACK RIGHT-POINTING TRIANGLE}'


class Paginated:
    """Represents a paginated message."""

    def __init__(self, message, *, per_page):
        """
        :param message: the message to paginate; the fields in the message embed are paginated
        :param per_page: the number of fields to show per page
        """
        self.message = message
        self.fields = message['embed']['fields']
        self.per_page = per_page
        self.num_pages = math.ceil(len(self.fields) / per_page)

        self.bot = None
        self.cur_page = None
        self.sent_message = None
        self.time_delay = None
        self.expire_handle = None
        self.tag = self.__class__.__name__ + str(time.time())
        self.logger = logging.getLogger(self.__class__.__qualname__)

    def _set_page(self, page_num):
        """Set current page to ``page_num``."""
        end = page_num * self.per_page
        begin = end - self.per_page
        self.cur_page = page_num
        self.message['embed']['fields'] = self.fields[begin:end]
        if self.num_pages > 1:
            self.message['embed']['footer'] = {'text': f'Page {page_num} / {self.num_pages}'}

    def schedule_unregister_after(self, time_delay):
        """Schedule unregister after a delay if that is later than current expiry time."""
        loop = asyncio.get_running_loop()
        time_expire = loop.time() + time_delay
        if self.expire_handle is not None:
            if time_expire < self.expire_handle.when():
                return
            self.expire_handle.cancel()
        self.expire_handle = loop.call_at(when=time_expire, callback=self.unregister)

    async def send(self, bot, channel_id, *, page_num=1, time_active, time_delay):
        """Send a paginated message.

        :param bot: the Bot instance to send the message through
        :param channel_id: the channel ID to send the mssage to
        :param page_num: the page number to display initially
        :param time_active: the time for which the message will be active
        :param time_delay: the time delay between last attempt to change pages and deactivation
        """
        self.bot = bot
        self._set_page(page_num)
        self.sent_message = await bot.client.send_message(self.message, channel_id)
        if self.num_pages <= 1:
            # No need to paginate.
            return
        await asyncio.sleep(0.5)
        await self.bot.client.add_reaction(self.sent_message.channel_id, self.sent_message.id, EMOJI_PREV)
        await asyncio.sleep(0.5)  # Delay to avoid 429
        await self.bot.client.add_reaction(self.sent_message.channel_id, self.sent_message.id, EMOJI_NEXT)
        bot.client.register_listener(EventType.MESSAGE_REACTION_ADD, self.tag, self._on_reaction_add_or_remove)
        bot.client.register_listener(EventType.MESSAGE_REACTION_REMOVE, self.tag, self._on_reaction_add_or_remove)
        self.logger.info(f'Paginating stuff')
        self.time_delay = time_delay
        self.schedule_unregister_after(time_active)

    async def _on_reaction_add_or_remove(self, data):
        """Event listener that is triggered when a reaction is added or removed."""
        if data['user_id'] == self.bot.client.user['id']:
            return
        if data['message_id'] != self.sent_message.id:
            return
        emoji = data['emoji'].get('name')
        if emoji not in (EMOJI_PREV, EMOJI_NEXT):
            return
        changed = False
        if emoji == EMOJI_PREV:
            if self.cur_page > 1:
                self._set_page(self.cur_page - 1)
                changed = True
        else:
            if self.cur_page < self.num_pages:
                self._set_page(self.cur_page + 1)
                changed = True
        if changed:
            partial_message = {'embed': self.message['embed']}
            await self.bot.client.edit_message(self.sent_message.channel_id, self.sent_message.id, partial_message)
            self.logger.debug(f'Updated page')
        self.schedule_unregister_after(self.time_delay)

    def unregister(self):
        """Delete all reactions on paginated message to signify deactivation and remove registered listeners."""
        self.logger.info('Removing paginator listeners')
        asyncio.create_task(self.bot.client.delete_all_reactions(self.sent_message.channel_id, self.sent_message.id))
        self.bot.client.unregister_listener(EventType.MESSAGE_REACTION_ADD, self.tag)
        self.bot.client.unregister_listener(EventType.MESSAGE_REACTION_REMOVE, self.tag)


async def paginate_and_send(message, bot, channel_id, *, per_page, initial_page=1, time_active, time_delay):
    """Convenience method to paginate and send the given message."""
    paginated = Paginated(message, per_page=per_page)
    await paginated.send(bot, channel_id, page_num=initial_page, time_active=time_active, time_delay=time_delay)
