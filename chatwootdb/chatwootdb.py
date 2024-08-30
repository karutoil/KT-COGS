from redbot.core import commands, Config
import discord
from discord.ext import commands, tasks
import psycopg2

class chatwootdb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_db_settings = {}  # Dictionary to store per-guild database settings
        self.guild_connections = {}  # Dictionary to store active connections
        self.guild_last_chat_id = {}  # Dictionary to store the last chat ID for each guild
        self.check_new_chats.start()

    def cog_unload(self):
        self.check_new_chats.cancel()
        for connection in self.guild_connections.values():
            connection.close()

    def get_db_connection(self, guild_id):
        if guild_id not in self.guild_connections:
            settings = self.guild_db_settings.get(guild_id)
            if not settings:
                return None
            connection = psycopg2.connect(
                dbname=settings['db_name'],
                user=settings['db_user'],
                password=settings['db_password'],
                host=settings['db_host'],
                port=settings['port']
            )
            self.guild_connections[guild_id] = connection
        return self.guild_connections[guild_id]

    def set_db_settings(self, guild_id, db_name, db_user, db_password, db_host, db_port):
        self.guild_db_settings[guild_id] = {
            'db_name': db_name,
            'db_user': db_user,
            'db_password': db_password,
            'db_host': db_host,
            'db_port': db_port
        }

    @tasks.loop(seconds=15)
    async def check_new_chats(self):
        for guild_id in self.guild_db_settings:
            connection = self.get_db_connection(guild_id)
            if connection:
                last_chat_id = self.guild_last_chat_id.get(guild_id)
                with connection.cursor() as cursor:
                    if last_chat_id:
                        query = "SELECT * FROM conversations WHERE id > %s ORDER BY id ASC"
                        cursor.execute(query, (last_chat_id,))
                    else:
                        query = "SELECT * FROM conversations ORDER BY id ASC LIMIT 1"
                        cursor.execute(query)
                    
                    new_chats = cursor.fetchall()

                    if new_chats:
                        for chat in new_chats:
                            chat_id = chat[0]  # Assuming the ID is the first column
                            customer_name = chat[1]  # Adjust this to match your table structure
                            initial_message = chat[2]  # Adjust this to match your table structure

                            await self.create_chat_channel(guild_id, chat_id, customer_name, initial_message)
                            self.guild_last_chat_id[guild_id] = chat_id

    async def create_chat_channel(self, guild_id, chat_id, customer_name, initial_message):
        guild = self.bot.get_guild(guild_id)
        if guild:
            channel_name = f"chat-{chat_id}"
            channel = await guild.create_text_channel(name=channel_name)
            await channel.send(f"Chat ID: {chat_id}")
            await channel.send(f"Customer: {customer_name}")
            await channel.send(f"Initial Message: {initial_message}")

    @commands.command()
    @commands.guild_only()
    async def set_db(self, ctx, db_name, db_user, db_password, db_host, db_port):
        """Sets the database configuration for this guild."""
        self.set_db_settings(ctx.guild.id, db_name, db_user, db_password, db_host, db_port)
        await ctx.send(f"Database settings have been configured for this guild.")

async def setup(bot):
    await bot.add_cog(chatwootdb(bot))
