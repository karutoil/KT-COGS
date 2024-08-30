import asyncpg
from redbot.core import commands, Config
from redbot.core.i18n import Translator
import asyncio

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
        async def _query_every_15_seconds():
            while True:
                try:
                    await self.query_table()
                except Exception as e:
                    print(f"An error occurred: {e}")
                await asyncio.sleep(900)  # Sleep for 15 minutes

        self._query_task = None
        self.loop = asyncio.get_event_loop()
        
        if not hasattr(self, '_query_task'):
            self._query_task = self.loop.create_task(_query_every_15_seconds())

    async def cog_load(self):
        super().cog_load()
        if not hasattr(self, '_query_task'):
            loop = asyncio.get_event_loop()
            self._query_task = loop.create_task(self.query_every_15_seconds())
            
    async def cog_unload(self):
        await self._query_task
        self.pools.clear()
        delattr(self, '_query_task')  # Clearing the task to avoid circular reference when garbage collecting

    async def get_channel_id(self, guild) -> str:
        pool = await self.get_pool(guild.id)
        try: 
            query = "SELECT id FROM public.conversations ORDER BY id DESC LIMIT 1"
            async with pool.acquire() as conn:
                results = await conn.fetch(query)

            if results:  
                max_id = sorted([int(record['id']) for record in results])[-1]
            else:
                max_id = 0

        except Exception as e: 
            print(f"An error occurred while querying the database: {e}")
            max_id = 0
        
        return max_id + 1
  

    async def generate_channel_name(self, guild) -> str:
        channel_id = await self.get_channel_id(guild)
        return f'Chat - {channel_id}'


    async def create_text_channel(self, name):
        for server in self.bot.guilds:
            if server == name.split()[0]:
                guild = server

        return await guild.create_text_channel(name)


    async def query_table(self, guild_id):
        pool = await self.get_pool(guild_id)
        try:  
            query = "SELECT id FROM public.conversations ORDER BY id ASC"
            async with pool.acquire() as conn:
                results = await conn.fetch(query)

            if results: 
                for result in results:
                    channel_name = await self.generate_channel_name(result['id'])
                    channel = get(self.bot.get_all_channels(), name=channel_name)
                    
                    if not channel:
                        await self.create_text_channel(channel_name)  
        except Exception as e:  
            print(f"An error occurred while querying the database: {e}")

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
