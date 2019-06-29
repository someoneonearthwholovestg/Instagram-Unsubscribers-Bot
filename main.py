import asyncio

from TelegramApp import TelegramApp


async def periodic_unsubs_check_task():
    SECONDS_TO_WAIT = 60 * 60 * 60
    while True:
        await telegram_app.new_unfollowers(username='fightLikeABrave', only_new_unsubs=True)
        await asyncio.sleep(SECONDS_TO_WAIT)

if __name__ == '__main__':
    TOKEN = '672100742:AAEj-1j0E-BMjOW6nyuuha6DGpgifIY_EBc'
    telegram_app = TelegramApp(TOKEN)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([
        telegram_app.start_schedule_tasks(),
        telegram_app.start_responding(),
    ]))
