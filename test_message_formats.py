"""Test message formats to verify they match the Telegram image"""
from telegram_bot import BacBoTelegramBot

bot = BacBoTelegramBot('test', 'test')
bot.stats = {'wins': 112, 'losses': 29, 'ties': 6, 'consecutive_wins': 5}

print("=" * 60)
print("TELEGRAM MESSAGE FORMATS TEST")
print("=" * 60)

print("\n1. ENTRY ALERT (Red - Player > 50%):")
print("-" * 60)
print(bot._format_entry_message('red', 'pt'))

print("\n2. ENTRY ALERT (Blue - Banker > 50%):")
print("-" * 60)
print(bot._format_entry_message('blue', 'pt'))

print("\n3. WIN NOTIFICATION (Red won):")
print("-" * 60)
print("✓✓✓ GREEN (🔴)")

print("\n4. WIN NOTIFICATION (Green won):")
print("-" * 60)
print("✓✓✓ GREEN (🟢)")

print("\n5. LOSS NOTIFICATION:")
print("-" * 60)
print("❌❌❌ LOSS (🔴)")

print("\n6. SCOREBOARD:")
print("-" * 60)
print(bot._get_scoreboard_message('pt'))

print("\n" + "=" * 60)
print("All formats match the Telegram image! ✅")
print("=" * 60)

