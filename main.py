import asyncio

from TelegramApp import TelegramApp

def main(*args, **kwargs):
    TOKEN = '672100742:AAEj-1j0E-BMjOW6nyuuha6DGpgifIY_EBc'
    telegram_app = TelegramApp(TOKEN)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([
        telegram_app.start_schedule_tasks(),
        telegram_app.start_responding(),
    ]))

if __name__ == '__main__':
    main()

