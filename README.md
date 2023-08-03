# tg-dnd
Telegram Do Not Disturb — set status emoji with curl.

## usage

```bash
curl localhost:8000/status/stopsign
# I am busy, don't message me

curl localhost:8000/status/green-circle
# Free to hang out

curl localhost:8000/status/weed-pepe
# 420 Friday
```

## commands

- are sent to **Saved Messages** (PM to yourself).
- only **premium** emojis are supported.

#### `!dnd emoji alias`

Save new alias (override existing)

#### `!dnd?`

List all aliases.


## run

1. [Telegram **API_ID**, **API_HASH**](https://docs.telethon.dev/en/stable/basic/signing-in.html#signing-in) → `secrets.env`
2. `docker compose run tg-dnd`
3. `docker compose up -d`

## development

`pipenv install --dev`

## license

MIT
