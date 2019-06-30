import asyncio
import logging
import os


MODE = os.getenv('MODE')

def main():
    from TelegramApp import TelegramApp

    TOKEN = os.getenv('TOKEN')
    telegram_app = TelegramApp(TOKEN)
    loop = asyncio.get_event_loop()

    if MODE == 'dev':
        loop.create_task(telegram_app.start_polling())
    elif MODE == 'prod' or MODE == 'debug_webhook':
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        loop.create_task(telegram_app.start_webhook(url='https://{}.herokuapp.com/{}'.format(HEROKU_APP_NAME, TOKEN),
                                                    listen='0.0.0.0',
                                                    port=PORT))
    else:
        logging.error('No MODE specified!')
        exit(1)

    loop.create_task(telegram_app.start_schedule_tasks())

    loop.run_forever()

if __name__ == '__main__':
    if MODE == 'debug_webhook' or MODE == 'dev':
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()

