import discord
import asyncio
import httpx
from redbot.core import commands, Config

class chatwoot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
#        self.config.register_global(
#            chatwoot_api_key="",
#            chatwoot_url="",
#            channel_category_id=0
#        )
        self.bg_task = self.bot.loop.create_task(self.poll_chatwoot())

    async def poll_chatwoot(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.check_for_new_conversations()
            except Exception as e:
                print(f"Error while polling Chatwoot: {e}")
            await asyncio.sleep(15)  # Poll every 15 seconds

    async def check_for_new_conversations(self):
        api_key = await self.config.chatwoot_api_key()
        base_url = await self.config.chatwoot_url()

        headers = {
            'api_access_token': f'{api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(f"https://chat.heavisidehosting.com/api/v1/accounts/1/conversations", headers=headers)
                response.raise_for_status()
                conversations = response.json()

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

        customer_email = chat['customer']['email']
        creation_time = chat['created_at']
        messages = chat['messages']
        chat_url = chat['url']

        embed = discord.Embed(title="New Chat Started", color=discord.Color.blue())
        embed.add_field(name="Customer Email", value=customer_email, inline=False)
        embed.add_field(name="Chat URL", value=chat_url, inline=False)
        embed.add_field(name="Chat Created At", value=creation_time, inline=False)

        messages_text = "\n".join([f"{msg['created_at']}: {msg['content']}" for msg in messages])
        embed.add_field(name="Messages", value=messages_text if messages_text else "No messages yet.", inline=False)

        await channel.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def set_chatwoot_config(self, ctx, api_key: str, base_url: str, category_id: int):
        """Command to set Chatwoot configuration"""
        await self.config.chatwoot_api_key.set(api_key)
        await self.config.chatwoot_url.set(base_url)
        await self.config.channel_category_id.set(category_id)
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

def setup(bot):
    bot.add_cog(chatwoot(bot))
