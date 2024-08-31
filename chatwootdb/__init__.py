from .chatwootdb import chatwootdb
from redbot.core.utils import get_end_user_data_statement

__red_end_user_data_statement__ = get_end_user_data_statement(__file__)
print("init")


async def setup(bot):
    await bot.add_cog(chatwootdb(bot))