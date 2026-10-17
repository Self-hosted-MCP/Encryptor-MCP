# Connect your AI app

Any app that speaks MCP can use Encryptor MCP. It works with your Cryptomator vaults. There are two ways an app can reach it:

- **On the same computer (`stdio`).** The app starts its own small copy of Encryptor MCP. No login and no web address needed. You need the command installed (see [below](#before-you-start-install-the-command)).
- **Over the internet (your own server).** The app connects to `https://your-domain/mcp`. The first time, you type the server passphrase once and tick which vaults the app may ask for and whether it may change files. You need [your own server](setup-own-server.md) (Docker). Phone apps and web apps (claude.ai, ChatGPT) use this way.

```mermaid
flowchart LR
    subgraph computer["On the same computer: stdio"]
        A1["Claude Desktop, Claude Code, Codex,<br/>Cursor, VS Code, Gemini CLI, OpenClaw,<br/>Hermes, Goose, Cline, Zed, Kiro, ..."] -->|"starts it"| S1["Encryptor MCP"]
    end
    subgraph internet["Over the internet: your own server"]
        A2["Claude website and phone,<br/>ChatGPT, any app"] -->|"https + passphrase"| S2["Encryptor MCP"]
    end
    S1 --> V["Your vaults"]
    S2 --> V
```

**Your vault passwords stay with you.** The AI never sees or types a vault password. When it needs a vault, it asks to unlock it. You type the password on a page in your own browser (or in a password box on a Mac) and choose how long the vault stays open. Never put a vault password in an app's MCP settings or in the chat.

Menus in these apps change often. If a label below doesn't match what you see, look for "MCP", "Connectors" or "Tools" in the app's settings.

| App | Same computer | Over the internet |
|---|---|---|
| [Claude Code](#claude-code) | Yes | Yes |
| [Claude Desktop](#claude-desktop) | Yes, or the [extension](claude-desktop-extension.md) | Yes, via claude.ai |
| [Claude website and phone app](#claude-website-and-phone-app) | No | Yes |
| [ChatGPT](#chatgpt) | No | Yes |
| [Codex](#codex) | Yes | Yes |
| [Cursor](#cursor) | Yes | Yes |
| [VS Code (Copilot)](#vs-code) | Yes | Yes |
| [Gemini CLI](#gemini-cli) | Yes | Yes |
| [OpenClaw](#openclaw) | Yes | Yes |
| [Hermes Agent](#hermes-agent) | Yes | Yes |
| [Goose](#goose) | Yes | Yes |
| [Cline](#cline) | Yes | Yes |
| [Roo Code](#roo-code) | Yes | Yes |
| [Continue](#continue) | Yes | Yes |
| [Windsurf (Devin Desktop)](#windsurf-devin-desktop) | Yes | Yes |
| [Zed](#zed) | Yes | Yes |
| [LM Studio](#lm-studio) | Yes | Yes |
| [OpenCode](#opencode) | Yes | Yes |
| [Kiro](#kiro) | Yes | Yes |
| [GitHub Copilot CLI](#github-copilot-cli) | Yes | Yes |
| [Amp](#amp) | Yes | Yes |
| [Warp](#warp) | Yes | Yes |
| [JetBrains AI Assistant](#jetbrains-ai-assistant) | Yes | Yes |
| [Qwen Code](#qwen-code) | Yes | Yes |
| [Crush](#crush) | Yes | Yes |
| [Augment Code](#augment-code) | Yes | Yes |
| [Any other MCP app](#any-other-mcp-app) | Usually | If it supports MCP login (OAuth) |

The app-by-app settings below follow each app's own documentation as of October 2026, linked under each app. Tell us in an [issue](https://github.com/s17sh70x2jfl031ag/Encryptor-MCP/issues/new) if one has changed.

## Before you start: install the command

For the same-computer way you need [uv](https://docs.astral.sh/uv/). Then install Encryptor MCP:

```bash
uv tool install git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP
```

The command is now `encryptor-mcp`. Your app starts it with the argument `stdio`.

Desktop apps sometimes can't find commands that your terminal finds. Get the full path once:

- Mac and Linux: `which encryptor-mcp` (usually `/Users/you/.local/bin/encryptor-mcp`)
- Windows: `where encryptor-mcp`

Use that full path wherever you see `/full/path/to/encryptor-mcp` below.

## Tell it where your vaults are

You can do this in one of three ways:

- **The control center.** This is your own page for Encryptor MCP. Once your app is connected, ask it: *"Open my Encryptor control center."* Add your vaults there.
- **The settings file.** Put this line in `~/.config/encryptor-mcp/.env`:

  ```
  ENCRYPTOR_VAULTS=Personal=/path/to/Personal;Work=/path/to/Work
  ```

- **In the app's MCP settings.** Add `ENCRYPTOR_VAULTS` to the `env` block, as in the examples below. This is optional: leave it out if you use the control center or the settings file.

Each vault is a name, an `=` and the folder of the Cryptomator vault. Separate vaults with `;`. This is only where the vaults are, never their passwords.

## Claude Code

Same computer:

```bash
claude mcp add encryptor -s user -- encryptor-mcp stdio
```

Over the internet:

```bash
claude mcp add encryptor -s user --transport http https://your-domain/mcp
```

Then run `/mcp` inside Claude Code, choose `encryptor` and log in.

## Claude Desktop

The easiest way is the [Claude Desktop extension](claude-desktop-extension.md): one click to install.

Already installed the command ([above](#before-you-start-install-the-command))? Settings → Developer → **Edit Config** opens `claude_desktop_config.json`. Add:

```json
{
  "mcpServers": {
    "encryptor": {
      "command": "/full/path/to/encryptor-mcp",
      "args": ["stdio"],
      "env": { "ENCRYPTOR_VAULTS": "Personal=/path/to/Personal;Work=/path/to/Work" }
    }
  }
}
```

The `env` line is optional. Save, then quit and reopen Claude Desktop. To use the internet version instead, add it on the Claude website (below): connectors you add there also show up in Claude Desktop.

## Claude website and phone app

You add the connector on the website, and the phone app picks it up.

1. On [claude.ai](https://claude.ai), open **Settings → Connectors**.
2. Click **Add custom connector**. Name: `Encryptor MCP`. URL: `https://your-domain/mcp`.
3. Click **Connect**. The login page opens: tick the vaults Claude may ask for, choose whether it may change files, type your server passphrase and click **Allow access**.
4. In a chat, turn the connector on from the tools menu.
5. Open the Claude phone app: the connector is already there.

> [!TIP]
> In the connector's settings you can set tools to **Always ask**, so any change waits for your tap.

## ChatGPT

ChatGPT connects over the internet, through **developer mode**. Which plans can use it, and whether it allows changes (write actions), changes over time: check [OpenAI's developer mode page](https://help.openai.com/en/articles/12584461) for your plan.

1. **Settings → Apps & Connectors → Advanced settings →** turn on **Developer mode**.
2. **Create** a connector. URL: `https://your-domain/mcp`. Authentication: **OAuth**.
3. Save, then tick the vaults and type your server passphrase on the login page that opens.

## Codex

Same computer:

```bash
codex mcp add encryptor -- encryptor-mcp stdio
```

Over the internet:

```bash
codex mcp add encryptor --url https://your-domain/mcp
```

```bash
codex mcp login encryptor
```

Both write to `~/.codex/config.toml`, which you can also edit by hand:

```toml
[mcp_servers.encryptor]
command = "encryptor-mcp"
args = ["stdio"]

[mcp_servers.encryptor.env]
ENCRYPTOR_VAULTS = "Personal=/path/to/Personal;Work=/path/to/Work"
```

The `env` part is optional.

## Cursor

In `~/.cursor/mcp.json` (or Settings → MCP → Add):

```json
{
  "mcpServers": {
    "encryptor": {
      "command": "/full/path/to/encryptor-mcp",
      "args": ["stdio"],
      "env": { "ENCRYPTOR_VAULTS": "Personal=/path/to/Personal;Work=/path/to/Work" }
    }
  }
}
```

The `env` line is optional. Over the internet, use `"encryptor": { "url": "https://your-domain/mcp" }` instead.

## VS Code

Run **MCP: Add Server** from the command palette, or put this in `.vscode/mcp.json`:

```json
{
  "servers": {
    "encryptor": { "type": "stdio", "command": "/full/path/to/encryptor-mcp", "args": ["stdio"] }
  }
}
```

Over the internet, use `"encryptor": { "type": "http", "url": "https://your-domain/mcp" }`.

## Gemini CLI

In `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] }
  }
}
```

Over the internet, use `"encryptor": { "httpUrl": "https://your-domain/mcp" }`.

## OpenClaw

In `~/.openclaw/openclaw.json` (or Settings → MCP in the OpenClaw app, or `openclaw mcp add`):

```json5
{
  mcp: {
    servers: {
      encryptor: { command: "/full/path/to/encryptor-mcp", args: ["stdio"] }
    }
  }
}
```

Over the internet, use `encryptor: { url: "https://your-domain/mcp", transport: "streamable-http", auth: "oauth" }`, then run `openclaw mcp login encryptor` and type your server passphrase in the browser. If you use OpenClaw's **Sign in** button instead, the login returns to your OpenClaw address, so add that address to `ALLOWED_REDIRECT_HOSTS` ([below](#if-the-login-page-refuses-your-app)).

> [!WARNING]
> OpenClaw runs tools without asking, by default. To be asked before each change, run `openclaw mcp configure encryptor --approval prompt`.

## Hermes Agent

In `~/.hermes/config.yaml` (or with `hermes mcp add`):

```yaml
mcp_servers:
  encryptor:
    command: "/full/path/to/encryptor-mcp"
    args: ["stdio"]
```

Over the internet:

```yaml
mcp_servers:
  encryptor:
    url: "https://your-domain/mcp"
    auth: oauth
```

Run `/reload-mcp` in Hermes (or restart it). It opens the login page in your browser. To log in again later: `hermes mcp login encryptor`.

## Goose

In `~/.config/goose/config.yaml`, or with `goose configure` → Add Extension:

```yaml
extensions:
  encryptor:
    name: encryptor
    cmd: encryptor-mcp
    args: [stdio]
    enabled: true
    type: stdio
    timeout: 300
```

Over the internet, use `type: streamable_http` and `uri: https://your-domain/mcp` (the key is `uri`, not `url`) instead of `cmd` and `args`. Goose signs in with OAuth by itself. ([Goose docs](https://goose-docs.ai/docs/getting-started/using-extensions))

## Cline

MCP Servers icon → Configure → **Configure MCP Servers** opens `cline_mcp_settings.json`:

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"], "disabled": false, "autoApprove": [] } } }
```

Over the internet: `"encryptor": { "type": "streamableHttp", "url": "https://your-domain/mcp" }`. Set `type` to `streamableHttp`: left out, Cline uses the older SSE. In the Cline CLI, `cline mcp` has "Run or rerun browser authorization" for the login. ([Cline docs](https://docs.cline.bot/mcp/configuring-mcp-servers))

## Roo Code

**Edit Global MCP** (or **Edit Project MCP** for `.roo/mcp.json`):

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"], "disabled": false, "alwaysAllow": [] } } }
```

Over the internet: `"encryptor": { "type": "streamable-http", "url": "https://your-domain/mcp" }`. ([Roo Code docs](https://roocodeinc.github.io/Roo-Code/features/mcp/using-mcp-in-roo))

## Continue

Add a file in `.continue/mcpServers/`, for example `encryptor.yaml` (MCP works in Agent mode):

```yaml
name: encryptor
version: 0.0.1
schema: v1
mcpServers:
  - name: encryptor
    type: stdio
    command: encryptor-mcp
    args:
      - stdio
```

Over the internet: `type: streamable-http` and `url: https://your-domain/mcp` instead of `command` and `args`. ([Continue docs](https://docs.continue.dev/customize/deep-dives/mcp))

## Windsurf (Devin Desktop)

Cascade panel `...` → **Open MCP config file**:

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] } } }
```

Over the internet: `"encryptor": { "serverUrl": "https://your-domain/mcp" }`. OAuth login is supported. ([Windsurf docs](https://docs.devin.ai/desktop/cascade/mcp))

## Zed

Settings → AI → MCP Servers → **Add Server**, or in `settings.json`:

```json
"context_servers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"], "env": {} } }
```

Over the internet: `"encryptor": { "url": "https://your-domain/mcp" }`. Zed asks you to log in through MCP's OAuth. By default Zed asks before each tool call (`agent.tool_permissions`). ([Zed docs](https://zed.dev/docs/ai/mcp))

## LM Studio

Program tab → Install → **Edit mcp.json** (LM Studio 0.3.17 or newer). It uses the same format as Cursor:

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] } } }
```

Over the internet: `"encryptor": { "url": "https://your-domain/mcp" }`. ([LM Studio docs](https://lmstudio.ai/docs/app/mcp))

## OpenCode

In `opencode.json`:

```json
{ "$schema": "https://opencode.ai/config.json", "mcp": { "encryptor": { "type": "local", "command": ["encryptor-mcp", "stdio"], "enabled": true } } }
```

Over the internet: `"encryptor": { "type": "remote", "url": "https://your-domain/mcp", "enabled": true }`. The login starts by itself, or run `opencode mcp auth encryptor`. ([OpenCode docs](https://opencode.ai/docs/mcp-servers/))

## Kiro

In `~/.kiro/settings/mcp.json` (or `.kiro/settings/mcp.json` in a project):

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"], "disabled": false, "autoApprove": [] } } }
```

Over the internet: `"encryptor": { "url": "https://your-domain/mcp" }`. The browser login starts by itself when Kiro connects. ([Kiro docs](https://kiro.dev/docs/mcp/configuration/))

## GitHub Copilot CLI

```bash
copilot mcp add encryptor -- encryptor-mcp stdio
```

Over the internet:

```bash
copilot mcp add --transport http encryptor https://your-domain/mcp
```

Both write to `~/.copilot/mcp-config.json`. ([GitHub docs](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-mcp-servers))

## Amp

```bash
amp mcp add encryptor -- encryptor-mcp stdio
```

Over the internet:

```bash
amp mcp add encryptor https://your-domain/mcp
```

Opening Amp then starts the browser login by itself. The settings live under `amp.mcpServers` in `~/.config/amp/settings.json`. ([Amp docs](https://ampcode.com/docs/customize/mcp))

## Warp

Settings → Agents → MCP servers → **+ Add**:

```json
{ "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] } }
```

Over the internet: `{ "encryptor": { "url": "https://your-domain/mcp" } }`. Starting it opens the browser login. ([Warp docs](https://docs.warp.dev/knowledge-and-collaboration/mcp))

## JetBrains AI Assistant

Settings → Tools → AI Assistant → Model Context Protocol (MCP) → **Add**:

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] } } }
```

Over the internet: `"encryptor": { "url": "https://your-domain/mcp" }`. ([JetBrains docs](https://www.jetbrains.com/help/ai-assistant/mcp.html))

## Qwen Code

```bash
qwen mcp add encryptor encryptor-mcp stdio
```

Over the internet:

```bash
qwen mcp add --transport http encryptor https://your-domain/mcp
```

In `~/.qwen/settings.json` the internet key is `httpUrl` (`url` means the older SSE). Manage the login in the `/mcp` dialog. ([Qwen Code docs](https://qwenlm.github.io/qwen-code-docs/en/users/features/mcp/))

## Crush

In `~/.config/crush/crushrc`:

```bash
mcp add encryptor --command encryptor-mcp --args stdio
```

Over the internet:

```bash
mcp add encryptor --type http --url https://your-domain/mcp --oauth true
```

Crush asks before every tool call by default. ([Crush docs](https://github.com/charmbracelet/crush/blob/main/docs/config/README.md))

## Augment Code

Augment panel menu → Settings → MCP → **+** (or **Import from JSON**):

```json
{ "mcpServers": { "encryptor": { "command": "encryptor-mcp", "args": ["stdio"] } } }
```

Over the internet (**+ Add remote MCP**): `"encryptor": { "type": "http", "url": "https://your-domain/mcp" }`. ([Augment docs](https://docs.augmentcode.com/setup-augment/mcp))

## Any other MCP app

- **On the same computer:** the command is `encryptor-mcp` with the argument `stdio`. Vaults come from the control center, from `~/.config/encryptor-mcp/.env`, or from `ENCRYPTOR_VAULTS` in the app's `env` block.
- **Over the internet:** the address is `https://your-domain/mcp` (Streamable HTTP), with MCP's standard OAuth login: the app registers itself, then opens the login page.

Without installing anything, `uvx` can run it straight from GitHub:

```json
{ "command": "uvx", "args": ["--from", "git+https://github.com/s17sh70x2jfl031ag/Encryptor-MCP", "encryptor-mcp", "stdio"],
  "env": { "ENCRYPTOR_VAULTS": "Personal=/path/to/Personal" } }
```

The `env` line is optional.

## Is it working?

Ask your AI: *"Which Encryptor vaults can you see?"* It should list your vaults. When you ask it to read something inside one, it asks you to unlock it: type the password on the page that opens in your browser, not in the chat.

## Give it a name on the unlock page

The unlock page shows which app is asking. Most apps send their own name. If yours shows up as "AI app", set `ENCRYPTOR_APP_NAME` in the app's `env` block (for example `"Claude Code"`).

## If the login page refuses your app

This is only for the internet way. Only apps from a list of known addresses may receive the login: Claude, ChatGPT, OpenAI and VS Code on the web, plus any app on your own computer (localhost), which covers most desktop and command-line apps above. If another app shows "Redirect not allowed", add its domain to `ALLOWED_REDIRECT_HOSTS` in your server's settings.

---

Encryptor MCP works with Cryptomator vaults. It is not made by or affiliated with Cryptomator.
