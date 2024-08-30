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
        """Check for new chats on Chatwoot and create a channel called 'test'."""
        api_key = await self.config.chatwoot_api_key()
        account_id = await self.config.chatwoot_account_id()
        chatwoot_url = await self.config.chatwoot_url()
        
        if not api_key or not account_id:
            await ctx.send("Chatwoot credentials are not set.")
            return

        headers = {
            "Content-Type": "application/json",
            "api_access_token": api_key,
        }

        response = requests.get(
            f"https://{chatwoot_url}/api/v1/accounts/{account_id}/conversations",
            headers=headers
        )
        response = requests.get(chatwoot_url, headers=headers)
        if response.status_code == 200:
            conversations = response.json().get("payload", [])

        for conversation in conversations:
            if conversation["status"] == "open":
                channel_name = f"test-{conversation['uuid']}"
                guild = ctx.guild
                existing_channel = discord.utils.get(guild.channels, name=channel_name)
                if not existing_channel:
                    await guild.create_text_channel(channel_name)
                    await ctx.send(f"Channel '{channel_name}' created.")
                else:
                    await ctx.send(f"Channel '{channel_name}' already exists.")

def setup(bot: Red):
    bot.add_cog(chatwoot(bot))