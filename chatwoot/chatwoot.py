import discord
from redbot.core import commands
from requests.exceptions import RequestException

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

        async def _log_request(method, endpoint, data=None):
            message = f"API Request: {method}, Endpoint: {endpoint}"
            if data is not None:
                message += ", Data: " + str(data)
            self.logger.info(message)

            try:
                response = requests.request(method, endpoint, json=data)
            except RequestException as e:
                self.logger.error("Error fetching data from Chatwoot:", exc_info=True)
                await ctx.send(f"Error fetching data from Chatwoot: {str(e)}")
                return

            if response.status_code != 200:
                self.logger.warning("API Response Status Code: %s", response.status_code)
                self.logger.warning("API Response: %s", response.text)

        try:
            await _log_request(
                "GET",
                f"https://{chatwoot_url}/api/v1/accounts/{account_id}/conversations",
                headers=headers,
            )

            if response.status_code == 200:
                conversations = response.json().get("payload", [])
                new_conversations = []

                for conv in conversations:
                    if last_seen_chat_id is None or conv['id'] > last_seen_chat_id:
                        new_conversations.append(conv)

                if new_conversations:
                    # Update the last seen chat ID
                    await self.config.last_seen_chat_id.set(new_conversations[0]['id'])

                    guild = ctx.guild
                    existing_channel = discord.utils.get(guild.channels, name="test")
                    if not existing_channel:
                        await guild.create_text_channel("test")
                        await ctx.send("Channel 'test' created.")
                    else:
                        await ctx.send("Channel 'test' already exists.")
                else:
                    await ctx.send("No new chats found.")
        except RequestException as e:
            self.logger.error("Error fetching data from Chatwoot:", exc_info=True)
            await ctx.send(f"Error fetching data from Chatwoot: {str(e)}")

def setup(bot: Red):
    bot.add_cog(chatwoot(bot))