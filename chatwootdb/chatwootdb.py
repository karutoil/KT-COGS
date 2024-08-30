import asyncpg
from redbot.core import commands, Config
from redbot.core.i18n import Translator
from discord.ext import tasks

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

    async def cog_load(self):
        self.check_db.start()  # Start the task when the cog loads

    async def cog_unload(self):
        self.check_db.cancel()  # Stop the task when the cog unloads
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

    @tasks.loop(seconds=15)
    async def check_db(self):
        for guild_id, pool in self.pools.items():
            async with pool.acquire() as connection:
                query = "SELECT id FROM public.conversations WHERE new_data = TRUE;"  # Adjust query as needed
                result = await connection.fetch(query)
                
                if result:
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        for record in result:
                            channel_name = f"Chat - {record['id']}"
                            # Check if the channel already exists
                            existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
                            if not existing_channel:
                                # Create the text channel
                                new_channel = await guild.create_text_channel(channel_name)
                                await new_channel.send(f"New conversation started with ID: {record['id']}")
                            # Mark data as processed (adjust the query as needed)
                            await connection.execute("UPDATE public.conversations SET new_data = FALSE WHERE id = $1", record['id'])

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

    @db.command(name='update')
    async def update_db(self, ctx, *, query: str):
        """Updates data in the configured database"""
        pool = await self.get_pool(ctx.guild.id)
        async with pool.acquire() as connection:
            await connection.execute(query)
        
        await ctx.send("Data updated successfully.")

    @db.command(name='delete')
    async def delete_db(self, ctx, *, query: str):
        """Deletes data from the configured database"""
        pool = await self.get_pool(ctx.guild.id)
        async with pool.acquire() as connection:
            await connection.execute(query)
        
        await ctx.send("Data deleted successfully.")

def setup(bot):
    bot.add_cog(chatwootdb(bot))
