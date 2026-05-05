import discord
import os
import json
import sys

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
intents.voice_states = True

client = discord.Client(intents=intents)

# Node.jsサーバーにデータをJSON形式で送信する関数
def send_to_web(event_type, data):
    try:
        # flush=True をつけることでNode.js側ですぐに読み取れるようにする
        print(json.dumps({"event": event_type, "data": data}), flush=True)
    except Exception as e:
        pass

@client.event
async def on_ready():
    print(f'Botが起動しました: {client.user}', flush=True)
    
    # 起動時に最初のサーバー（Guild）の全情報を取得してWebへ送る
    if client.guilds:
        guild = client.guilds[0]
        channels = [{"id": str(c.id), "name": c.name} for c in guild.channels if str(c.type) == "text"]
        members = [{"id": str(m.id), "name": m.display_name, "status": str(m.status), "avatar": m.display_avatar.url if m.display_avatar else ""} for m in guild.members if not m.bot]
        
        send_to_web("init", {
            "guild_name": guild.name,
            "channels": channels,
            "members": members
        })

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    # コンソール用ログ（前回の機能）
    print(f'[メッセージ] #{message.channel.name} | {message.author}: {message.content}', flush=True)
    
    # Web画面用データ送信
    send_to_web("message", {
        "channel_id": str(message.channel.id),
        "author": message.author.display_name,
        "avatar": message.author.display_avatar.url if message.author.display_avatar else "",
        "content": message.content
    })

@client.event
async def on_presence_update(before, after):
    if after.bot:
        return
        
    old_status = str(before.status) if before else 'offline'
    new_status = str(after.status)

    if old_status != new_status:
        # コンソール用ログ（前回の機能）
        print(f'[ステータス] {after} が {new_status} になりました。', flush=True)
        # Web画面用データ送信
        send_to_web("presence", {
            "id": str(after.id),
            "status": new_status
        })

@client.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    # コンソール用ログ（前回の機能）
    old_channel = before.channel
    new_channel = after.channel
    if old_channel is None and new_channel is not None:
        print(f'[通話] {member} が 🔊{new_channel.name} に参加しました。', flush=True)
    elif old_channel is not None and new_channel is None:
        print(f'[通話] {member} が 🔊{old_channel.name} から退出しました。', flush=True)

token = os.environ.get('DISCORD_TOKEN')
if token:
    client.run(token)
else:
    print("エラー: 環境変数 'DISCORD_TOKEN' が見つかりません。", flush=True)