# Discord AI Chatbot

## Features And Commands

<details>
<summary><strong>Features (Click to expand)</strong></summary>

- [x] Free LLM Access: Uses a free language model to provide AI-powered responses at no cost.
- [x] Secure Configuration: Protects sensitive credentials by storing them in environment variables instead of hardcoding them.
- [x] Hybrid Command System: Supports `!remember` commands and natural-language messaging for flexible interaction.
- [x] Persistent Memory: Remembers important information across conversations for future reference.

</details>

<details>
<summary><strong>Commands (Click to expand)</strong></summary>

- [x] `!remember`: Allows users to save information for the bot to recall later.

</details>

# Setup

### Step 1. Download the repository
Download or clone the repository from GitHub.

### Step 2. Run Setup
Double-click `Setup.bat`. This automatically installs Ollama and downloads the required AI model.

### Step 3. Create a Discord bot
Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.

1. Create a new application.
2. Navigate to the **Bot** section.
3. Create your bot and copy its token.
4. Enable the required intents.
5. Invite your bot to your Discord server.

### Step 4. Configure your bot token
Open the `.env` file and paste your Discord bot token.

```env
DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
```

### Step 5. Start the bot
Double-click `Start.bat` to launch your Discord AI chatbot.

-----------------

### Using Docker to run 
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
- Have a working bot token
- Follow up to step 4
#### Install docker-compose on a Linux machine:
For Debian-based distributions (such as Ubuntu):
```
apt update -y; sudo apt upgrade -y; sudo apt autoremove -y; sudo apt install docker-compose -y
```
