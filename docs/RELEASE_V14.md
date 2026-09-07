# Fenix Messenger v14

## Что реально изменено

- React source больше не содержит пустой `App` — есть рабочий desktop/mobile shell.
- Чат-лист, папки, архив, stories strip, поиск.
- Chat header, pinned message, message bubbles, composer.
- Profile и Settings панели.
- Создание группы.
- Адаптивный mobile режим.
- Архитектурный документ без копирования Telegram Desktop исходников.
- Оригинальные Fenix визуальные ассеты.
- Backend из предыдущей версии сохранён: FastAPI, PostgreSQL/SQLAlchemy, email OTP, WebSocket.

## Проверка

- `python -m compileall backend`
- `python -m pytest -q`
- `npm run build`
- `unzip -t FenixMessenger_V14_TDESKTOP_INSPIRED.zip`
