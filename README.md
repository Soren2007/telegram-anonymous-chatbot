# Telegram Anonymous Chat Bot

This project enables anonymous messaging between Telegram users by leveraging a Python-based worker and a D1 database. The bot allows users to send and receive messages without revealing their identities.

## Features

- ✅ Anonymous messaging between Telegram users
- ✅ Secure user management via D1 database
- ✅ Inline keyboard for message replies
- ✅ Webhook-based real-time message processing
- ✅ Encryption for data security

## Installation & Setup

### 1️⃣ Clone the Repository
Clone the project to your local machine:

```sh
git clone https://github.com/your-repo/telegram-anonymous-chat.git
cd telegram-anonymous-chat
```

### 2️⃣ Create a Python Worker
Ensure your environment supports Python execution.

### 3️⃣ Set Up D1 Database
Create a database and bind it to your worker:

```sql
CREATE TABLE users (
  "id" INTEGER PRIMARY KEY,
  "telegram_user_id" TEXT,
  "rkey" TEXT,
  "target_user" TEXT
);
```

### 4️⃣ Configure Webhook
Open the worker in a browser and visit:

```
https://yourworker.username.workers.dev/init
```

### 5️⃣ Update Configuration
Modify the following variables in `main.py` with your bot credentials:

```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
BOT_ID = "YOUR_BOT_ID"
ALLOWED = "ALL"  # Set to "ALL" or specify usernames
```

## Usage

### 🤖 Start the Bot
Send `/start` to initiate anonymous messaging.

### 📩 Create an Anonymous Link
Click **"Create an anonymous link for me ✅"**, then copy and share your unique link.

### ✉️ Sending Anonymous Messages
Recipients receive anonymous messages, and can reply using inline buttons.

## Security & Encryption

- 🔒 Uses MD5 hashing for webhook authentication
- 🔐 Encrypts user reply callback data with XOR and Base64 encoding

## License

This project is licensed under the **GPL License**.

## Author

Created by **SORENSHAMLOU**, Version `1.0.0`.

---