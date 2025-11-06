"""
Telegram bot for sending Bac Bo game alerts
"""
from telegram import Bot
from telegram.error import TelegramError
import logging
import asyncio
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Use a single shared event loop for all Telegram operations to avoid connection pool issues
_shared_loop = None
_loop_lock = threading.Lock()
_loop_thread = None

def _get_shared_loop():
    """Get or create a shared event loop for Telegram operations"""
    global _shared_loop, _loop_thread
    
    with _loop_lock:
        if _shared_loop is None or _shared_loop.is_closed():
            import sys
            if sys.platform == 'win32':
                _shared_loop = asyncio.SelectorEventLoop()
            else:
                _shared_loop = asyncio.new_event_loop()
            
            # Start the loop in a daemon thread
            def run_loop():
                asyncio.set_event_loop(_shared_loop)
                _shared_loop.run_forever()
            
            _loop_thread = threading.Thread(target=run_loop, daemon=True)
            _loop_thread.start()
        
        return _shared_loop

def _run_async(coro):
    """Run async coroutine using shared event loop"""
    import concurrent.futures
    
    loop = _get_shared_loop()
    
    # Schedule the coroutine on the shared loop
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    
    try:
        # Wait for result with timeout
        return future.result(timeout=30)
    except concurrent.futures.TimeoutError:
        logger.error("Telegram message send timed out")
        future.cancel()
        raise
    except Exception as e:
        logger.error(f"Error in async execution: {e}")
        future.cancel()
        raise


class BacBoTelegramBot:
    """Telegram bot for Bac Bo alerts"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        # Configure Bot with larger connection pool to avoid timeout errors
        if token:
            from telegram.request import HTTPXRequest
            # Use HTTPXRequest with increased connection pool size
            request = HTTPXRequest(connection_pool_size=20, read_timeout=30, write_timeout=30, connect_timeout=30)
            self.bot = Bot(token=token, request=request)
        else:
            self.bot = None
        self.stats = {
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'consecutive_wins': 0,
            'last_result': None
        }
        
    def _calculate_assertiveness_rate(self) -> float:
        """Calculate assertiveness rate"""
        total = self.stats['wins'] + self.stats['losses']
        if total == 0:
            return 100.0
        return (self.stats['wins'] / total) * 100
    
    def _get_scoreboard_message(self, language: str = 'en') -> str:
        """Generate scoreboard message"""
        assertiveness = self._calculate_assertiveness_rate()
        
        if language == 'pt':
            return (
                f"PLACAR\n"
                f"✓ :{self.stats['wins']}\n"
                f"🟢 :{self.stats['losses']}\n"
                f"🔴 :{self.stats['ties']}\n"
                f"📊 GANHOS SEGUIDOS: {self.stats['consecutive_wins']}\n"
                f"🎯 TAXA DE ASSERTIVIDADE: {assertiveness:.2f}%"
            )
        else:  # English
            return (
                f"SCOREBOARD\n"
                f"✓ :{self.stats['wins']}\n"
                f"🟢 :{self.stats['losses']}\n"
                f"🔴 :{self.stats['ties']}\n"
                f"📊 CONSECUTIVE WINS: {self.stats['consecutive_wins']}\n"
                f"🎯 ASSERTIVENESS RATE: {assertiveness:.2f}%"
            )
    
    def _format_entry_message(self, color: str, language: str = 'en') -> str:
        """
        Format entry confirmation message
        color: 'red' or 'blue' for player/banker
        """
        if color.lower() == 'red':
            color_emoji = '🔴'  # Red circle for player
        else:  # blue
            color_emoji = '🔵'  # Blue circle for banker
        
        tie_emoji = '🟢'  # Green circle for tie
        
        if language == 'pt':
            return (
                f"ENTRADA CONFIRMADA\n"
                f"🎲 ENTRAR NA COR ({color_emoji})\n"
                f"🎯 PROTEGER NO EMPATE ({tie_emoji})\n"
                f"💰💰🤖 Entrar No Jogo"
            )
        else:  # English
            return (
                f"CONFIRMED ENTRY\n"
                f"🎲 ENTER THE COLOR ({color_emoji})\n"
                f"🎯 PROTECT ON TIE ({tie_emoji})\n"
                f"💰💰🤖 Enter The Game"
            )
    
    def send_entry_alert(self, player_percent: float, banker_percent: float, language: str = 'en') -> bool:
        """
        Send entry confirmation alert when player odds are favorable
        Returns True if message was sent successfully
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        # Determine which color to bet on (red for player, blue for banker)
        # If player percent > 50%, bet on player (red)
        # Otherwise bet on banker (blue)
        if player_percent > 50:
            color = 'red'
            bet_on = 'player'
        else:
            color = 'blue'
            bet_on = 'banker'
        
        try:
            message = self._format_entry_message(color, language)
            _run_async(self.bot.send_message(chat_id=self.chat_id, text=message))
            logger.info(f"Sent entry alert: {bet_on} ({color})")
            return True
        except TelegramError as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending entry alert: {e}")
            return False
    
    def send_win_notification(self, result: str, winning_color: str = 'red', language: str = 'en') -> bool:
        """
        Send win notification
        result: 'win' or 'loss'
        winning_color: 'red' or 'green' - which color won (for win notifications)
        """
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        if result == 'win':
            self.stats['wins'] += 1
            self.stats['consecutive_wins'] += 1
            self.stats['last_result'] = 'win'
            
            # Win message format: "✓✓✓ GREEN (🟢)" or "✓✓✓ GREEN (🔴)"
            # The emoji shows which color won
            if winning_color.lower() == 'green':
                color_emoji = '🟢'
            else:  # red
                color_emoji = '🔴'
            
            message = f"✓✓✓ GREEN ({color_emoji})"
        else:  # loss
            self.stats['losses'] += 1
            self.stats['consecutive_wins'] = 0
            self.stats['last_result'] = 'loss'
            
            # Loss message format: "❌❌❌ LOSS (🔴)"
            message = "❌❌❌ LOSS (🔴)"
        
        try:
            _run_async(self.bot.send_message(chat_id=self.chat_id, text=message))
            
            # Send updated scoreboard
            scoreboard = self._get_scoreboard_message(language)
            _run_async(self.bot.send_message(chat_id=self.chat_id, text=scoreboard))
            
            logger.info(f"Sent {result} notification")
            return True
        except TelegramError as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending win notification: {e}")
            return False
    
    def send_scoreboard(self, language: str = 'en') -> bool:
        """Send current scoreboard"""
        if not self.bot:
            return False
        
        try:
            message = self._get_scoreboard_message(language)
            _run_async(self.bot.send_message(chat_id=self.chat_id, text=message))
            return True
        except TelegramError as e:
            logger.error(f"Error sending scoreboard: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending scoreboard: {e}")
            return False
    
    def send_message(self, text: str) -> bool:
        """Send a generic message"""
        if not self.bot:
            logger.error("Telegram bot not initialized")
            return False
        
        try:
            _run_async(self.bot.send_message(chat_id=self.chat_id, text=text))
            return True
        except TelegramError as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_startup_message(self, language: str = 'en') -> bool:
        """Send bot startup notification"""
        if language == 'pt':
            message = "🤖 Bot Bac Bo iniciado!\n\n📊 Monitorando o jogo...\n⏱️ Intervalo de verificação: 5 segundos\n🎯 Limite de alerta: Player > 98%"
        else:
            message = "🤖 Bac Bo Bot Started!\n\n📊 Monitoring game...\n⏱️ Check interval: 5 seconds\n🎯 Alert threshold: Player > 98%"
        
        return self.send_message(message)
    
    def send_shutdown_message(self, language: str = 'en') -> bool:
        """Send bot shutdown notification"""
        if language == 'pt':
            message = "🛑 Bot Bac Bo finalizado!\n\nO bot foi encerrado."
        else:
            message = "🛑 Bac Bo Bot Stopped!\n\nThe bot has been shut down."
        
        return self.send_message(message)
    
    def send_status_update(self, stats: Optional[Dict] = None, language: str = 'en') -> bool:
        """Send status update with current statistics"""
        if not self.bot:
            return False
        
        try:
            if stats:
                player_pct = stats.get('player_percent', 0)
                banker_pct = stats.get('banker_percent', 0)
                tie_pct = stats.get('tie_percent', 0)
                
                if language == 'pt':
                    message = (
                        f"📊 Status Atual\n\n"
                        f"👤 Jogador: {player_pct}%\n"
                        f"🏦 Banca: {banker_pct}%\n"
                        f"🤝 Empate: {tie_pct}%\n\n"
                        f"{'✅ Condição de alerta ativada!' if player_pct > 50 else '⏳ Aguardando condição favorável...'}"
                    )
                else:
                    message = (
                        f"📊 Current Status\n\n"
                        f"👤 Player: {player_pct}%\n"
                        f"🏦 Banker: {banker_pct}%\n"
                        f"🤝 Tie: {tie_pct}%\n\n"
                        f"{'✅ Alert condition met!' if player_pct > 50 else '⏳ Waiting for favorable condition...'}"
                    )
            else:
                if language == 'pt':
                    message = (
                        "⚠️ Não foi possível obter estatísticas do jogo.\n\n"
                        "Possíveis causas:\n"
                        "• Site pode estar bloqueando acesso automatizado\n"
                        "• Página pode não estar carregando completamente\n"
                        "• Conteúdo do jogo pode estar em iframe não detectado\n\n"
                        "O bot continua monitorando..."
                    )
                else:
                    message = (
                        "⚠️ Could not retrieve game statistics.\n\n"
                        "Possible causes:\n"
                        "• Site may be blocking automated access\n"
                        "• Page may not be loading completely\n"
                        "• Game content may be in undetected iframe\n\n"
                        "The bot continues monitoring..."
                    )
            
            _run_async(self.bot.send_message(chat_id=self.chat_id, text=message))
            return True
        except TelegramError as e:
            logger.error(f"Error sending status update: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending status update: {e}")
            return False

