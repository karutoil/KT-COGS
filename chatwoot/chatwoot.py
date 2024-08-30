import discord
import requests
from redbot.core import commands, Config
from redbot.core.bot import Red

class chatwoot(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(chatwoot_api_key=None, chatwoot_account_id=None)

    @commands.command()
    async def set_chatwoot_credentials(self, ctx, api_key: str, account_id: int):
        """Set Chatwoot API key and account ID."""
        await self.config.chatwoot_api_key.set(api_key)
        await self.config.chatwoot_account_id.set(account_id)
        await ctx.send("Chatwoot credentials set.")

    @commands.command()
    async def set_chatwoot_url(self, ctx, chatwoot_url: str):
        """Set Chatwoot URL."""
        await self.config.chatwoot_url.set(chatwoot_url)
        await ctx.send("Chatwoot URL set.")

    @commands.command()
    async def check_new_chats(self, ctx):
        """Check for new chats on Chatwoot and create a channel with the chat ID."""
        api_key = await self.config.chatwoot_api_key()
        account_id = await self.config.chatwoot_account_id()
        chatwoot_url = await self.config.chatwoot_url()
        last_seen_chat_id = await self.config.last_seen_chat_id()
        if not api_key or not account_id:
            await ctx.send("Chatwoot credentials are not set.")
            return
        headers = {
            "Content-Type": "application/json",
            "api_access_token": api_key,
        }
        response = requests.get(
            f"{chatwoot_url}/api/v1/accounts/{account_id}/conversations",
            headers=headers
        )
        if response.status_code == 200:
            conversations = response.json().get("payload", [])
            new_conversations = []
            for conv in conversations:
                if last_seen_chat_id is None or conv['id'] > last_seen_chat_id:
                    new_conversations.append(conv)
            if new_conversations:
                # Update the last seen chat ID
                await self.config.last_seen_chat_id.set(new_conversations[-1]['id'])
                guild = ctx.guild
                for conv in new_conversations:
                    existing_channel = discord.utils.get(guild.channels, name=str(conv['id']))
                    if not existing_channel:
                        await guild.create_text_channel(str(conv['id']))
                        await ctx.send(f"Channel '{conv['id']}' created.")
                await ctx.send(f"New chats found and {len(new_conversations)} channels created.")
            else:
                await ctx.send("No new chats found. Last seen chat ID: " + str(last_seen_chat_id))
        else:
            await ctx.send(f"Error fetching data from Chatwoot: {response.status_code}")
            await ctx.send(f"Response: {response.text}")

def setup(bot: Red):
    """
    Load the chatwoot cog into the bot.

    This function is called by discord.py when the cog is loaded.
    """
    bot.add_cog(chatwoot(bot))