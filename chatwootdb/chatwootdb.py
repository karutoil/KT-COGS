import asyncio
import asyncpg
from redbot.core import commands, Config
from redbot.core.i18n import Translator
import discord

_ = Translator("chatwootdb", __file__)

class chatwootdb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)  # Unique identifier for your cog
        self.config.register_guild(
            db_user=None,
            db_password=None,
            db_name=None,
            db_host=None,
            db_port=5432
        )
        self.pools = {}  # Dictionary to hold connection pools per server
        self.task = None  # Task to run the check_new_chats function

    async def cog_load(self):
        self.task = asyncio.create_task(self.check_new_chats())

    async def cog_unload(self):
        if self.task:
            self.task.cancel()
        for pool in self.pools.values():
            await pool.close()

    async def get_pool(self, guild_id):
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

    async def check_new_chats(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for guild_id in self.pools:
                pool = await self.get_pool(guild_id)
                async with pool.acquire() as connection:
                    result = await connection.fetch("SELECT * FROM public.conversations WHERE created_at > NOW() - INTERVAL '20 seconds'")
                    if result:
                        for record in result:
                            await self.create_chat_channel(self.bot.get_guild(guild_id), record['id'])
            await asyncio.sleep(15)

    async def create_chat_channel(self, guild, chat_id):
        category_id = 1093031434974937128
        category = discord.utils.get(guild.categories, id=category_id)
        if not category:
            print(f"Category with ID {category_id} not found in guild {guild.name}")
            return

        channel_name = f"Chat - {chat_id}"
        existing_channel = discord.utils.get(category.text_channels, name=channel_name)
        if existing_channel:
            print(f"Channel {channel_name} already exists")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        print(f"Created channel {channel_name}")

    @commands.group(name='db')
    @commands.guild_only()
    async def db(self, ctx):
        """Database management commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @db.command(name='setconfig')
    @commands.has_permissions(administrator=True)
    async def set_config(self, ctx, user: str, password: str, database: str, host: str, port: int = 5432):
        """Sets the database configuration for this server"""
        await self.config.guild(ctx.guild).db_user.set(user)
        await self.config.guild(ctx.guild).db_password.set(password)
        await self.config.guild(ctx.guild).db_name.set(database)
        await self.config.guild(ctx.guild).db_host.set(host)
        await self.config.guild(ctx.guild).db_port.set(port)
        await ctx.send("Database configuration updated.")

    @db.command(name='query')
    async def query_db(self, ctx, *, query: str):
        """Executes a query on the configured database"""
        pool = await self.get_pool(ctx.guild.id)
        async with pool.acquire() as connection:
            result = await connection.fetch(query)
        
        if result:
            result_str = '\n'.join([str(record) for record in result])
            await ctx.send(f"Query result:\n{result_str}")
        else:
            await ctx.send("No results found.")

    @db.command(name='insert')
    async def insert_db(self, ctx, *, query: str):
        """Inserts data into the configured database"""
        pool = await self.get_pool(ctx.guild.id)
        async with pool.acquire() as connection:
            await connection.execute(query)
        
        await ctx.send("Data inserted successfully.")

def setup(bot):
    bot.add_cog(chatwootdb(bot))