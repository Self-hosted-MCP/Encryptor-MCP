# Every setting

Most people never touch a setting by hand. You add vaults and choose what the AI may do on the [control center](control-center.md). This page lists everything else, for when you want it.

Every setting is optional, except a passphrase for the server version.

## Where settings come from

Settings can live in three places:

1. **The control center** (your own page in the browser). It keeps its choices in `state/settings.json`, inside your config folder.
2. **Environment variables.** These are settings handed to a program when it starts: the `env` block in your AI app's settings, Docker's `environment:`, or a hosting company's "Variables" page.
3. **The settings file**, `~/.config/encryptor-mcp/.env` (on Windows `%USERPROFILE%\.config\encryptor-mcp\.env`, in Docker `/data/.env`). One `NAME=value` per line, `#` for comments, no quotes needed.

When two places disagree:

- **The control center wins** for the vault list, vault names and folders, what the AI may do with each vault, the default vault and auto-lock times. Values in the settings file are only where things start; once you change something on the page, the page's choice counts.
- **An environment variable wins over the settings file**, as long as it isn't empty.
- **`ENCRYPTOR_READ_ONLY` is fixed when you set it.** When it's set in an environment variable or the settings file (on or off), the control center's switch shows it but can't change it.
- **`ENCRYPTOR_CONFIG_DIR`, `ENCRYPTOR_DATA_DIR`, `ENCRYPTOR_ENV_FILE` and `ENCRYPTOR_APP_NAME`** are read from environment variables only, never from the settings file.

A template with the settings people set, each explained in one line: [`.env.example`](../.env.example).

> [!NOTE]
> Restart your AI app (or the server) after changing `ENCRYPTOR_MAX_HOURS`, `ENCRYPTOR_FINDER`, `HOST`, `PORT`, `PUBLIC_URL` or `ALLOWED_REDIRECT_HOSTS`, and after changing any environment variable. Also restart after switching a vault to or from **Read and change**: the AI app only gets the tools that change files when it starts ([why](tools.md#limits)).

## The control center's settings

Open the control center and choose **Settings** at the top. How to open it: [control-center.md](control-center.md#opening-it).

| Section | What you do there |
|---|---|
| **Vaults** | Every vault, with what the AI may do, its own auto-lock time and whether it's the default. **Settings** opens that vault's own settings |
| **Add a vault** | Add a Cryptomator vault you already have: a name, its folder, and what the AI may do |
| **Create a new vault** | Make a brand new vault, with a password and a recovery key |
| **Auto-lock** | How long a vault may sit unused before it locks: 5, 10, 15, 30 or 60 minutes |
| **Safety** | **Read only for every AI app**, and whether **AI apps may ask to delete the trash for good** |
| **Connect an AI app** | On a server only: the address to add to your AI app |

Each vault's own settings page has these sections:

| Section | What you do there |
|---|---|
| (top card) | Whether it's open, its folder, and its format |
| **The AI may** | **Read and change**, **Read only** or **Hidden from AI**, plus the **Default vault** box |
| **Auto-lock** | Its own time, or **Same as all vaults** |
| **Password** | Change the vault's password |
| **Recovery key** | Show the recovery key (needs the password), or set a new password with it under **Forgot the password?** |
| **Name and folder** | **Rename** it, or **Change** the folder it points at |
| **Remove** | **Remove from the list**. The vault and its files stay where they are |

The **About** page has the update check: [Updates](#updates) below.

## Vaults

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_VAULTS` | Your vaults, as `Name=/path/to/vault;Other=/path/to/other`. Each path is the folder that holds `vault.cryptomator`. `~` means your home folder | none |
| `ENCRYPTOR_MODES` | What the AI may do with each vault: `Name=read,Other=hidden`. Modes are `full` (read and change), `read` and `hidden`. A mode the program doesn't know becomes `read`, the safe one | `full` |

Vaults you add on the control center don't need these at all. More about modes: [vaults-and-apps.md](vaults-and-apps.md).

## Unlocking and auto-lock

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_IDLE_MINUTES` | Lock a vault after this many minutes without use. The control center's **Auto-lock** wins once you save it there | `10` |
| `ENCRYPTOR_MAX_HOURS` | Never keep a vault open longer than this many hours, whatever you choose when unlocking | `12` |
| `ENCRYPTOR_UNLOCK` | How you're asked for the password. `auto`: the AI app opens the unlock page if it can, else a Mac password box, else the AI gives you a link. `page`: the app opens the page, else a link. `box`: a Mac password box, else a link. `link`: always a link | `auto` |

The Mac password box keeps the vault open **Until I lock it** (still with auto-lock and the 12 hour limit), and has no read only option. Use the unlock page when you want those choices.

## Approvals

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_ASK_BEFORE` | Also ask you before these, comma separated: `replace` (writing over an existing file), `trash`, `move` | none |
| `ENCRYPTOR_APPROVE` | How you're asked. `auto`: a Mac box, else your AI app's own question, else a one-time code the AI asks you about in the chat. `box`: the Mac box, else the code. `ask`: the app's own question, else the code. `code`: always the code | `auto` |

Deleting for good (emptying the trash) is always approved by you, and **never** with a code in the chat: only with the Mac box, your AI app's own question, or the **Delete for good** button on the control center. Details: [tools.md](tools.md#asking-first).

## Safety

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_READ_ONLY` | `on`: no AI app may change anything in any vault. When set to any value here, the control center's switch is fixed to it | off (the switch on the page decides) |

Whether **AI apps may ask to delete the trash for good** is a switch on the control center only (**Settings**, **Safety**). It's on by default, and you still approve each time.

`on`, `yes`, `true` and `1` mean on. Anything else means off.

## Mac

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_FINDER` | `off` hides **Show in Finder** on a vault's page. Any other value keeps it | `on` (Docker: `off`) |

## Language

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_LANGUAGE` | Show the pages in one language, like `de`, `ja` or `pt-BR`, whatever the browser asks for. Codes and how to add a language: [languages.md](languages.md) | empty (follow the browser's language) |

## Updates

There is no setting in the file for this. The update check is a switch on the control center's **About** page: **Check GitHub for a new version once a day**. It's off by default. When on, it asks GitHub for the newest release once a day and sends nothing about you. More: [updates.md](updates.md).

## Server version (`encryptor-mcp serve`)

| Setting | What it does | Default |
|---|---|---|
| `LOGIN_PASSPHRASE` | The passphrase for the control center and for connecting AI apps, 8 or more characters | none (required) |
| `LOGIN_HASH` | The same passphrase, stored only as a hash. `encryptor-mcp set-passphrase` writes it into the settings file. Wins over `LOGIN_PASSPHRASE` | none |
| `PUBLIC_URL` | The address people and AI apps use, like `https://vault.example.com`. Must start with `https://`, unless it's `localhost` or `127.0.0.1` | `http://localhost:8767` |
| `HOST` | The network address the server listens on | `127.0.0.1` (Docker: `0.0.0.0`) |
| `PORT` | The port it listens on | `8767` |
| `ALLOWED_REDIRECT_HOSTS` | Websites allowed to receive an AI app's login, comma separated (`localhost` always is). Setting it **replaces** the list, so copy the defaults when you add one | `claude.ai,claude.com,chatgpt.com,openai.com,vscode.dev` |
| `ENCRYPTOR_DOMAIN` | Used by `docker-compose.yml` only: your server's name, for the HTTPS certificate and `PUBLIC_URL` | none |

`RENDER_EXTERNAL_URL` and `RAILWAY_PUBLIC_DOMAIN` are set by those hosting companies by themselves. The server reads them to find its address when `PUBLIC_URL` is empty.

## Folders and names (environment only)

| Setting | What it does | Default |
|---|---|---|
| `ENCRYPTOR_CONFIG_DIR` | The config folder | `~/.config/encryptor-mcp` (Docker: `/data`) |
| `ENCRYPTOR_ENV_FILE` | Another settings file | `<config folder>/.env` |
| `ENCRYPTOR_DATA_DIR` | The data folder | `<config folder>/state` |
| `ENCRYPTOR_APP_NAME` | The app's name on the unlock page and in the record, when the AI app doesn't send its own | `AI app` |
| `ENCRYPTOR_DAV_DEBUG` | Any value: prints details about **Show in Finder** to the AI app's MCP log. For hunting a problem only | off |

## Files in your config folder

Your config folder is `~/.config/encryptor-mcp` (Windows: `%USERPROFILE%\.config\encryptor-mcp`, Docker: `/data`).

| File or folder | What it is |
|---|---|
| `.env` | The settings file |
| `state/settings.json` | What you chose on the control center: vaults, modes, default vault, auto-lock, safety switches, update check |
| `state/update.json` | The result of the last update check |
| `state/fingerprints/` | Each vault's file fingerprints, for spotting cut or swapped files. Encrypted with a key made from the vault's own key |
| `state/readlogs/` | Each vault's read log: which files were opened, by whom and why. Encrypted, and chained so tampering shows |
| `locks/` | Small lock files, so two changes never run at the same time on this computer |
| `mounts/` | Where **Show in Finder** attaches open vaults (Mac) |
| `state/oauth.json` | Server only: the connected AI apps, with their tokens kept only as fingerprints |
| `state/sessions.json` | Server only: browsers you told to **Remember this browser for 90 days** |
| `state/signins.json` | Server only: sign-in attempts of the last 7 days. Never a passphrase |

On a computer, sign-ins to the control center live in memory only and end when your AI app closes.

Inside each vault there's also a hidden `.encryptor` folder, encrypted like everything else: the record of changes, earlier versions and the trash. See [undo-and-backups.md](undo-and-backups.md#the-hidden-encryptor-folder).

Nothing decrypted is ever written here. Vault passwords and keys stay in memory only.
