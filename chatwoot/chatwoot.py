import discord
from redbot.core import commands, Config
from woot import Chatwoot, AsyncChatwoot

class chatwoot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            chatwoot_api_key="",
            chatwoot_url="",
            channel_category_id=0
        )
        self.chatwoot_client = None
        conversations = async_chatwoot.conversations
        all_conversations = conversations.list(account_id=1)

    @commands.Cog.listener()
    async def on_ready(self):
        # Initialize the Chatwoot client
        api_key = await self.config.chatwoot_api_key()
        base_url = await self.config.chatwoot_url()
        async_chatwoot = AsyncChatwoot(api_key, base_url)
        print("ChatwootCog is ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Example: Fetching chat data from Chatwoot
        chats = self.chatwoot_client.chats.list()  # Modify this according to actual API endpoint
        for chat in chats:
            if chat['status'] == 'open':
                await self.create_chat_channel(chat)

    async def create_chat_channel(self, chat):
        category_id = await self.config.channel_category_id()
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
        conversations = async_chatwoot.conversations
        all_conversations = conversations.list(account_id=1)
        await ctx.send(f"Fetched {len(all_conversations)} chats from Chatwoot.")

def setup(bot):
    bot.add_cog(chatwoot(bot))
