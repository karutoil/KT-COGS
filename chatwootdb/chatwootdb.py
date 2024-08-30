from redbot.core import commands, Config
import discord
import asyncpg

class chatwootdb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_guild(
            db_user=None,
            db_password=None,
            db_name=None,
            db_host=None,
            db_port=5432
        )
        self.pool = None

    @commands.Cog.listener()
    async def on_ready(self, guild_id):
        if guild_id not in self.pools:
            config = await self.config.guild_from_id(guild_id).all()
            self.pools[guild_id] = await asyncpg.create_pool(
                user=config['db_user'],
                password=config['db_password'],
                database=config['db_name'],
                host=config['db_host'],
                port=config['db_port']
            )
        return self.pools[guild_id]
    
    @commands.command()
    async def create_chat_channel(self, ctx, chat_id: int):
        # Query the database for chat information
        async with self.pool.acquire() as connection:
            query = "SELECT * FROM conversations WHERE id = $1"
            chat_info = await connection.fetchrow(query, chat_id)

            if chat_info:
                channel_name = f"chat-{chat_id}"
                guild = ctx.guild

                # Create the channel
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    ctx.author: discord.PermissionOverwrite(read_messages=True),
                }
                channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

                # Send chat information in the new channel
                await channel.send(f"Chat ID: {chat_info['id']}\nChat Content: {chat_info['content']}")
            else:
                await ctx.send("Chat not found.")

async def setup(bot):
    await bot.add_cog(chatwootdb(bot))
