import discord
from discord.ext import commands, tasks
import socket
from datetime import datetime
import os
from typing import List, Dict

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get('TOKEN')

# ПЕРВАЯ ГРУППА СЕРВЕРОВ
SERVERS_GROUP1 = [
    {"ip": "62.122.214.155", "port": 27014, "name": "🎯 **CS:S МИКС #1**", "type": "mix"},
    {"ip": "62.122.214.155", "port": 27015, "name": "⚡ **CS:S МИКС #2**", "type": "mix"},
    {"ip": "62.122.214.155", "port": 27016, "name": "🔥 **CS:S МИКС #3**", "type": "mix"},
    {"ip": "62.122.214.155", "port": 27017, "name": "💫 **CS:S МИКС #4**", "type": "mix"},
    {"ip": "45.95.31.153", "port": 27015, "name": "🎪 **CS:S МИКС #5**", "type": "mix"},
    {"ip": "45.95.31.153", "port": 27115, "name": "🏆 **CS:S МИКС #6**", "type": "mix"},
    {"ip": "92.255.63.83", "port": 27215, "name": "⭐ **CS:S МИКС SIBERIA #1**", "type": "mix"},
    {"ip": "92.255.63.86", "port": 27115, "name": "✨ **CS:S МИКС SIBERIA #2**", "type": "mix"},
    {"ip": "45.95.31.134", "port": 27415, "name": "🎮 **CS:S МИКС TOXIC**", "type": "mix"},
]

# ВТОРАЯ ГРУППА СЕРВЕРОВ
SERVERS_GROUP2 = [
    {"ip": "45.136.204.58", "port": 27015, "name": "🌟 **ASTRUM PROJECT**", "type": "mix"},
    {"ip": "37.230.162.178", "port": 27015, "name": "💫 **ASTRUM PROJECT 2**", "type": "mix"},
    {"ip": "45.136.204.116", "port": 27015, "name": "💎 **DIAMOND #1**", "type": "mix"},
    {"ip": "45.136.204.116", "port": 27016, "name": "💎 **DIAMOND #2**", "type": "mix"},
    {"ip": "45.136.204.116", "port": 27019, "name": "⚔️ **DIAMOND 2x2 #1**", "type": "mix"},
    {"ip": "45.136.204.116", "port": 27020, "name": "⚔️ **DIAMOND 2x2 #2**", "type": "mix"},
]

# ТРЕТЬЯ ГРУППА СЕРВЕРОВ
SERVERS_GROUP3 = [
    {"ip": "46.174.51.165", "port": 27015, "name": "🎯 **1x1 ARENA**", "type": "1x1", "full_threshold": 10},
    {"ip": "46.174.51.165", "port": 27017, "name": "💣 **GRENADE TRAINING**", "type": "training", "full_threshold": 5},
    {"ip": "46.174.51.165", "port": 27018, "name": "🎯 **AIM BOT TRAINING**", "type": "training", "full_threshold": 4},
]

# ID каналов (ВСТАВЬТЕ СВОИ)
CHANNEL_ID_1 = 1476601497147150468  # Основные сервера
CHANNEL_ID_2 = 1476614532330946774  # Вставьте ID для ASTRUM & DIAMOND
CHANNEL_ID_3 = 1476617744471425064  # Вставьте ID для тренировочных
# ===============================

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
message_ids = {CHANNEL_ID_1: None, CHANNEL_ID_2: None, CHANNEL_ID_3: None}

def query_server(ip: str, port: int) -> Dict:
    """Запрос информации об одном сервере"""
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        
        # A2S_INFO запрос
        request = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        sock.sendto(request, (ip, port))
        
        # Получаем ответ
        response, addr = sock.recvfrom(4096)
        sock.close()
        
        if response[:4] != b'\xFF\xFF\xFF\xFF':
            return None
        
        data = response[4:]
        
        # Проверяем тип ответа (первые 4 байта уже убрали)
        if len(data) < 1:
            return None
            
        # Тип ответа (байт) - пропускаем
        data = data[1:]
        
        # Название сервера
        name_end = data.find(b'\x00')
        if name_end == -1:
            return None
        server_name = data[:name_end].decode('utf-8', errors='ignore').strip()
        data = data[name_end+1:]
        
        # Карта
        map_end = data.find(b'\x00')
        if map_end == -1:
            return None
        current_map = data[:map_end].decode('utf-8', errors='ignore').strip()
        data = data[map_end+1:]
        
        # Папка игры
        folder_end = data.find(b'\x00')
        if folder_end == -1:
            return None
        data = data[folder_end+1:]
        
        # Название игры
        game_end = data.find(b'\x00')
        if game_end == -1:
            return None
        data = data[game_end+1:]
        
        # ID игры (2 байта)
        if len(data) < 2:
            return None
        data = data[2:]
        
        # Количество игроков
        if len(data) < 1:
            return None
        players = data[0]
        data = data[1:]
        
        # Максимальное количество игроков
        if len(data) < 1:
            return None
        max_players = data[0]
        
        return {
            'name': server_name,
            'map': current_map,
            'players': players,
            'max_players': max_players,
            'online': True
        }
        
    except socket.timeout:
        if sock:
            sock.close()
        return None
    except ConnectionRefusedError:
        if sock:
            sock.close()
        return None
    except Exception as e:
        if sock:
            sock.close()
        return None
def get_servers_info(servers_list: List[Dict]) -> List[Dict]:
    """Получение информации о группе серверов"""
    servers_info = []
    
    for server in servers_list:
        info = query_server(server['ip'], server['port'])
        if info:
            servers_info.append({
                'display_name': server['name'],
                'ip': server['ip'],
                'port': server['port'],
                'name': info['name'],
                'map': info['map'],
                'players': info['players'],
                'max_players': info['max_players'],
                'server_type': server.get('type', 'mix'),
                'full_threshold': server.get('full_threshold'),
                'online': True
            })
        else:
            servers_info.append({
                'display_name': server['name'],
                'ip': server['ip'],
                'port': server['port'],
                'server_type': server.get('type', 'mix'),
                'full_threshold': server.get('full_threshold'),
                'online': False
            })
    
    return servers_info

def get_server_status(players: int, server_type: str, full_threshold: int = None):
    """Определяет статус сервера"""
    if full_threshold:
        if players >= full_threshold:
            return "🔥 ПОЛНЫЙ", "🔴"
        elif players >= full_threshold - 2:
            return "⚡ АКТИВНЫЙ", "🟠"
        elif players >= full_threshold - 4:
            return "📈 СРЕДНИЙ", "🟡"
        elif players > 0:
            return "📉 МАЛО", "🟢"
        else:
            return "💤 ПУСТО", "⚫"
    
    if server_type == "mix":
        if players >= 10:
            return "🔥 ПОЛНЫЙ", "🔴"
        elif players >= 7:
            return "⚡ АКТИВНЫЙ", "🟠"
        elif players >= 4:
            return "📈 СРЕДНИЙ", "🟡"
        elif players > 0:
            return "📉 МАЛО", "🟢"
        else:
            return "💤 ПУСТО", "⚫"
    
    return "📊 НЕИЗВЕСТНО", "⚪"

async def create_status_embed(servers_list: List[Dict], group_name: str):
    """Создание embed с статусом серверов"""
    servers_info = get_servers_info(servers_list)
    
    total_players = sum(s['players'] for s in servers_info if s.get('online', False))
    online_servers = sum(1 for s in servers_info if s.get('online', False))
    
    embed = discord.Embed(
        title=f"🎮 **CS:S - {group_name}**",
        description=(
            f"```📊 ОБЩАЯ СТАТИСТИКА```\n"
            f"**🟢 Онлайн серверов:** `{online_servers}/{len(servers_list)}`\n"
            f"**👥 Всего игроков:** `{total_players}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    for server in servers_info:
        if server['online']:
            status_emoji, border_color = get_server_status(
                server['players'], 
                server.get('server_type', 'mix'),
                server.get('full_threshold')
            )
            
            progress = int((server['players'] / server['max_players']) * 10)
            progress_bar = "█" * progress + "░" * (10 - progress)
            
            threshold_info = f" [полный при {server['full_threshold']}+]" if server.get('full_threshold') else ""
            
            server_box = (
                f"┌────────────────────────────────┐\n"
                f"│ {border_color} {server['display_name']}{threshold_info}\n"
                f"├────────────────────────────────┤\n"
                f"│ 📍 Карта: `{server['map']}`\n"
                f"│ 👥 Игроки: `{server['players']}/{server['max_players']}` {progress_bar}\n"
                f"│ 🔌 IP: `{server['ip']}:{server['port']}`\n"
                f"│ 📊 Статус: {status_emoji}\n"
                f"└────────────────────────────────┘"
            )
            
            embed.add_field(
                name=f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
                value=f"```{server_box}```",
                inline=False
            )
        else:
            offline_box = (
                f"┌────────────────────────────────┐\n"
                f"│ ❌ {server['display_name']}\n"
                f"├────────────────────────────────┤\n"
                f"│ 🔌 IP: `{server['ip']}:{server['port']}`\n"
                f"│ 📊 Статус: 💔 ОФФЛАЙН\n"
                f"└────────────────────────────────┘"
            )
            
            embed.add_field(
                name=f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
                value=f"```{offline_box}```",
                inline=False
            )
    
    embed.set_footer(text="🔄 Автообновление каждые 20 секунд")
    return embed

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} подключен!')
    print(f'Находится на серверах: {[guild.name for guild in bot.guilds]}')
    update_channels.start()

@tasks.loop(seconds=20)
async def update_channels():
    """Автоматическое обновление сообщений"""
    global message_ids
    
    channel1 = bot.get_channel(CHANNEL_ID_1)
    if channel1:
        embed1 = await create_status_embed(SERVERS_GROUP1, "ОСНОВНЫЕ СЕРВЕРА")
        await update_channel_message(channel1, embed1, CHANNEL_ID_1)
    
    channel2 = bot.get_channel(CHANNEL_ID_2)
    if channel2 and CHANNEL_ID_2 != 0:
        embed2 = await create_status_embed(SERVERS_GROUP2, "ASTRUM & DIAMOND")
        await update_channel_message(channel2, embed2, CHANNEL_ID_2)
    
    channel3 = bot.get_channel(CHANNEL_ID_3)
    if channel3 and CHANNEL_ID_3 != 0:
        embed3 = await create_status_embed(SERVERS_GROUP3, "ТРЕНИРОВОЧНЫЕ СЕРВЕРА")
        await update_channel_message(channel3, embed3, CHANNEL_ID_3)

async def update_channel_message(channel, embed, channel_id):
    """Обновление сообщения в конкретном канале"""
    global message_ids
    
    try:
        if message_ids[channel_id]:
            try:
                message = await channel.fetch_message(message_ids[channel_id])
                await message.edit(embed=embed)
                print(f"✅ Канал {channel_id} обновлен")
            except discord.NotFound:
                message = await channel.send(embed=embed)
                message_ids[channel_id] = message.id
        else:
            # Удаляем старые сообщения
            async for msg in channel.history(limit=20):
                if msg.author == bot.user:
                    await msg.delete()
            
            message = await channel.send(embed=embed)
            message_ids[channel_id] = message.id
            print(f"✨ Создано сообщение в канале {channel_id}")
    except Exception as e:
        print(f"❌ Ошибка в канале {channel_id}: {e}")

# Команда для принудительного обновления
@bot.command(name='обнови')
async def force_update(ctx):
    await update_channels()
    await ctx.send("✅ Статус обновлен!", delete_after=3)

# Команда для проверки конкретного сервера
@bot.command(name='сервер')
async def check_server(ctx, group: str = None, number: int = None):
    if not group or not number:
        await ctx.send("❌ Использование: `!сервер [основной/новый/тренир] [номер]`")
        return
    
    group_lower = group.lower()
    if group_lower == 'основной':
        servers = SERVERS_GROUP1
        group_name = "основных"
    elif group_lower == 'новый':
        servers = SERVERS_GROUP2
        group_name = "новых"
    elif group_lower == 'тренир':
        servers = SERVERS_GROUP3
        group_name = "тренировочных"
    else:
        await ctx.send("❌ Неправильная группа. Используйте `основной`, `новый` или `тренир`")
        return
    
    if number < 1 or number > len(servers):
        await ctx.send(f"❌ В группе {group_name} только {len(servers)} серверов")
        return
    
    server = servers[number-1]
    info = query_server(server['ip'], server['port'])
    
    if info:
        embed = discord.Embed(
            title=f"🎮 **{server['name']}**",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📍 **Карта**", value=f"`{info['map']}`", inline=True)
        embed.add_field(name="👥 **Игроки**", value=f"`{info['players']}/{info['max_players']}`", inline=True)
        embed.add_field(name="🔌 **IP:Порт**", value=f"`{server['ip']}:{server['port']}`", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ Сервер {server['name']} оффлайн")

# Команда для смены канала
@bot.command(name='канал')
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel: discord.TextChannel, group: str = None):
    global CHANNEL_ID_1, CHANNEL_ID_2, CHANNEL_ID_3, message_ids
    
    if not group:
        await ctx.send("❌ Укажите группу: `основной`, `новый` или `тренир`")
        return
    
    if group.lower() in ['основной', '1', 'осн']:
        CHANNEL_ID_1 = channel.id
        message_ids[CHANNEL_ID_1] = None
        await ctx.send(f"✅ Канал для **ОСНОВНЫХ** серверов изменен на {channel.mention}")
    elif group.lower() in ['новый', '2', 'нов']:
        CHANNEL_ID_2 = channel.id
        message_ids[CHANNEL_ID_2] = None
        await ctx.send(f"✅ Канал для **НОВЫХ** серверов изменен на {channel.mention}")
    elif group.lower() in ['тренир', '3', 'тре']:
        CHANNEL_ID_3 = channel.id
        message_ids[CHANNEL_ID_3] = None
        await ctx.send(f"✅ Канал для **ТРЕНИРОВОЧНЫХ** серверов изменен на {channel.mention}")
    else:
        await ctx.send("❌ Неправильная группа. Используйте `основной`, `новый` или `тренир`")
        return
    
    await update_channels()

# Запуск
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ТОКЕН НЕ НАЙДЕН! Добавьте переменную TOKEN в Railway Variables")
    else:
        print(f"✅ Токен загружен, запускаю бота...")
        bot.run(TOKEN)
