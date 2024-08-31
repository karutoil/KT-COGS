import discord
from redbot.core import commands, checks, Config
import asyncio
import psycopg2

class chatwootdb(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.config.register_global(
            db_host="localhost",
            db_name="your_database",
            db_user="your_username",
            db_password="your_password"
        )
        self.category_id = 1093031434974937128
        self.check_interval = 15  # seconds
        self.bot.loop.create_task(self.check_new_conversation())

    async def check_new_conversation(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                db_config = await self.config.all()
                conn = psycopg2.connect(
                    host=db_config['db_host'],
                    database=db_config['db_name'],
                    user=db_config['db_user'],
                    password=db_config['db_password']
                )
                cur = conn.cursor()
                cur.execute("SELECT MAX(id) FROM public.conversation")
                newest_id = cur.fetchone()[0]
                cur.close()
                conn.close()

                if newest_id is not None:
                    guild = discord.utils.get(self.bot.guilds, id=1093028183982473258)
                    category = discord.utils.get(guild.categories, id=self.category_id)
                    channel_name = f"Chat - {newest_id}"
                    if not discord.utils.get(category.text_channels, name=channel_name):
                        await category.create_text_channel(channel_name)
            except Exception as e:
                print(f"Error checking new conversation: {e}")
            finally:
                await asyncio.sleep(self.check_interval)

    @commands.command()
    @checks.is_owner()
    async def setdb(self, ctx, host: str, db_name: str, user: str, password: str):
        await self.config.db_host.set(host)
        await self.config.db_name.set(db_name)
        await self.config.db_user.set(user)
        await self.config.db_password.set(password)
        await ctx.send("Database configuration updated.")

def setup(bot):
    bot.add_cog(chatwootdb(bot))