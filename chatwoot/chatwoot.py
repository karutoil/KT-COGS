import discord
import asyncio
import httpx
from redbot.core import commands, Config

class chatwoot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.bg_task = self.bot.loop.create_task(self.poll_chatwoot())
        self.message_cache = {}  # Dictionary to cache last seen message IDs

    async def poll_chatwoot(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.check_for_new_conversations()
                await self.check_for_new_messages()
            except Exception as e:
                print(f"Error while polling Chatwoot: {e}")
            await asyncio.sleep(15)  # Poll every 15 seconds

    async def check_for_new_conversations(self):
        api_key = await self.config.chatwoot_api_key()

        headers = {
            'api_access_token': f'{api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"https://chat.heavisidehosting.com/api/v1/accounts/1/conversations", headers=headers)
                response.raise_for_status()
                data = response.json()

                conversations = data.get("data", {}).get("payload", [])

                for chat in conversations:
                    if chat['status'] == 'open':
                        channel_name = f"chat-{chat['id']}"
                        if discord.utils.get(self.bot.get_all_channels(), name=channel_name):
                            continue  # Skip if the channel already exists
                        await self.create_chat_channel(chat)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred while fetching conversations: {str(e)}")
        except Exception as e:
            print(f"An error occurred while fetching conversations: {str(e)}")

    async def create_chat_channel(self, chat):
        category_id = 1093031434974937128
        category = discord.utils.get(self.bot.get_guild(1093028183982473258).categories, id=category_id)

        if category is None:
            print(f"Category with ID {category_id} not found.")
            return

        channel_name = f"chat-{chat['id']}"
        channel = await category.create_text_channel(name=channel_name)

        customer_email = chat['meta']['sender'].get('email', 'No email provided')
        creation_time = chat.get('created_at', 'Unknown')
        chat_url = chat.get('uuid', 'No URL')

        embed = discord.Embed(title="New Chat Started", color=discord.Color.blue())
        embed.add_field(name="Customer Email", value=customer_email, inline=False)
        embed.add_field(name="Chat URL", value=chat_url, inline=False)
        embed.add_field(name="Chat Created At", value=creation_time, inline=False)

        await channel.send(embed=embed)
        # Cache the last message ID for this chat
        self.message_cache[chat['id']] = None

    async def check_for_new_messages(self):
        api_key = await self.config.chatwoot_api_key()

        headers = {
            'api_access_token': f'{api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"https://chat.heavisidehosting.com/api/v1/accounts/1/conversations", headers=headers)
                response.raise_for_status()
                data = response.json()

                conversations = data.get("data", {}).get("payload", [])

                for chat in conversations:
                    if chat['status'] == 'open':
                        channel_name = f"chat-{chat['id']}"
                        channel = discord.utils.get(self.bot.get_all_channels(), name=channel_name)

                        if channel:
                            last_message_id = self.message_cache.get(chat['id'])
                            messages = chat.get('messages', [])
                            new_messages = [msg for msg in messages if msg['id'] != last_message_id]

                            for msg in new_messages:
                                embed = discord.Embed(title="New Message", color=discord.Color.green())
                                embed.add_field(name="Sender", value=msg['meta']['sender'].get('email', 'Unknown'), inline=False)
                                embed.add_field(name="Message", value=msg['content'], inline=False)
                                await channel.send(embed=embed)

                                # Update the cached message ID
                                self.message_cache[chat['id']] = msg['id']
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred while fetching messages: {str(e)}")
        except Exception as e:
            print(f"An error occurred while fetching messages: {str(e)}")

    @commands.command()
    @commands.is_owner()
    async def set_chatwoot_config(self, ctx, api_key: str):
        """Command to set Chatwoot configuration"""
        await self.config.chatwoot_api_key.set(api_key)
        await ctx.send("Chatwoot configuration updated!")

    @commands.command()
    @commands.is_owner()
    async def test_chatwoot(self, ctx):
        """Command to test the Chatwoot integration"""
        api_key = await self.config.chatwoot_api_key()

        headers = {
            'api_access_token': f'{api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://chat.heavisidehosting.com/api/v1/accounts/1/conversations", headers=headers)
                response.raise_for_status()
                conversations = response.json()
                await ctx.send(f"Fetched {len(conversations)} chats from Chatwoot.")
        except httpx.HTTPStatusError as e:
            await ctx.send(f"HTTP error occurred: {str(e)}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def cog_unload(self):
        """This function is called when the cog is unloaded."""
        if hasattr(self, 'bg_task'):
            self.bg_task.cancel()

def setup(bot):
    bot.add_cog(chatwoot(bot))
