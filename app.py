import asyncio
import logging
import os

MODE_LOCAL_POLLING = 'local_polling'
MODE_REMOTE_POLLING = 'remote_polling'
MODE_REMOTE_WEBHOOK = 'remote_webhook'
MODE = os.getenv('MODE')

async def launch_reloadable_app(app):
    while True:
        try:
            await app()
        except Exception as e:
            logging.exception('Restarting server with exception: {}'.format(e))
            await asyncio.sleep(60)

def main():
    from TelegramApp import TelegramApp

    TOKEN = os.getenv('TOKEN')
    telegram_app = TelegramApp(TOKEN)
    loop = asyncio.get_event_loop()

    if MODE == MODE_LOCAL_POLLING:
        loop.create_task(telegram_app.start_polling())
        loop.create_task(telegram_app.start_schedule_tasks())
    elif MODE == MODE_REMOTE_POLLING:
        loop.create_task(launch_reloadable_app(telegram_app.start_polling()))
        loop.create_task(launch_reloadable_app(telegram_app.start_schedule_tasks()))
    elif MODE == MODE_REMOTE_WEBHOOK:
        logging.exception('Webhooks not implemented')
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        loop.create_task(telegram_app.start_webhook(url='https://{}.herokuapp.com/{}'.format(HEROKU_APP_NAME, TOKEN),
                                                    listen='0.0.0.0',
                                                    port=PORT))
        loop.create_task(launch_reloadable_app(telegram_app.start_schedule_tasks()))
    else:
        logging.error('No MODE specified!')
        exit(1)

    loop.run_forever()

if __name__ == '__main__':
    if MODE == MODE_LOCAL_POLLING or MODE == MODE_REMOTE_POLLING:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()

