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
    async def check_new_chats(self, ctx):
        """Check for new chats on Chatwoot and create a channel called 'test'."""
        api_key = await self.config.chatwoot_api_key()
        account_id = await self.config.chatwoot_account_id()
        
        if not api_key or not account_id:
            await ctx.send("Chatwoot credentials are not set.")
            return

        headers = {
            "Content-Type": "application/json",
            "api_access_token": api_key,
        }

        response = requests.get(
            f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations",
            headers=headers
        )

        if response.status_code == 200:
            conversations = response.json().get("payload", [])
            if conversations:
                # Create the 'test' channel
                guild = ctx.guild
                existing_channel = discord.utils.get(guild.channels, name="test")
                if not existing_channel:
                    await guild.create_text_channel("test")
                    await ctx.send("Channel 'test' created.")
                else:
                    await ctx.send("Channel 'test' already exists.")
            else:
                await ctx.send("No new chats found.")
        else:
            await ctx.send(f"Error fetching data from Chatwoot: {response.status_code}")

def setup(bot: Red):
    bot.add_cog(chatwoot(bot))