import discord
from discord.ext import tasks
from redbot.core import commands, Config
import aiohttp

class chatwoot(commands.Cog):
    """Cog to create channels based on new Chatwoot chats."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        self.config.register_global(last_seen_chat_id=0)
        self.session = aiohttp.ClientSession()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_for_new_chats.start()

    @tasks.loop(seconds=15)
    async def check_for_new_chats(self):
        api_key = await self.config.chatwoot_api_key()
        account_id = await self.config.chatwoot_account_id()
        chatwoot_url = await self.config.chatwoot_url()
        complete_chatwoot_url = f"{chatwoot_url}/api/v1/accounts/{account_id}/conversations"
        headers = {
            "Content-Type": "application/json",
            "api_access_token": api_key
        }

        async with self.session.get(complete_chatwoot_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                new_chats = [chat for chat in data['payload'] if chat['id'] > await self.config.last_seen_chat_id()]
                
                for chat in new_chats:
                    await self.create_channel_for_chat(chat)
                    await self.config.last_seen_chat_id.set(chat['id'])
            else:
                print(f"Failed to fetch chats: {response.status}")

    async def create_channel_for_chat(self, chat):
        account_id = await self.config.chatwoot_account_id()
        chatwoot_url = await self.config.chatwoot_url()
        guild = self.bot.get_guild(1093028183982473258)
        customer_email = chat['meta']['sender']['email']
        created_at = chat['created_at']
        messages = chat['messages']
        chat_url = f"{chatwoot_url}/app/accounts/{account_id}/conversations/{chat['id']}"

        channel_name = f"chat-{chat['id']}"
        channel = await guild.create_text_channel(channel_name)

        await channel.send(f"**Customer Email:** {customer_email}")
        await channel.send(f"**Chat Created At:** {created_at}")
        await channel.send(f"**Chat URL:** {chat_url}")

        for message in messages:
            await channel.send(f"{message['created_at']}: {message['content']}")

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

def setup(bot):
    bot.add_cog(chatwoot(bot))
