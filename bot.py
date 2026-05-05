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
        print(json.dumps({"event": event_type, "data": data}), flush=True)
    except Exception as e:
        pass

@client.event
async def on_ready():
    print(f'Botが起動しました: {client.user}', flush=True)
    
    if client.guilds:
        guild = client.guilds[0]
        # テキストチャンネルの取得
        channels = [{"id": str(c.id), "name": c.name} for c in guild.channels if str(c.type) == "text"]
        
        # ボイスチャンネルと現在入っているメンバーの取得
        voice_channels = [{"id": str(vc.id), "name": vc.name, "members": [str(m.id) for m in vc.members if not m.bot]} for vc in guild.voice_channels]
        
        # メンバー情報の取得
        members = [{"id": str(m.id), "name": m.display_name, "status": str(m.status), "avatar": m.display_avatar.url if m.display_avatar else ""} for m in guild.members if not m.bot]
        
        send_to_web("init", {
            "guild_name": guild.name,
            "channels": channels,
            "voice_channels": voice_channels, # 追加
            "members": members
        })

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    print(f'[メッセージ] #{message.channel.name} | {message.author}: {message.content}', flush=True)
    
    attachments = []
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith('image/'):
            attachments.append(attachment.url)
    
    send_to_web("message", {
        "channel_id": str(message.channel.id),
        "author": message.author.display_name,
        "avatar": message.author.display_avatar.url if message.author.display_avatar else "",
        "content": message.content,
        "attachments": attachments
    })

@client.event
async def on_presence_update(before, after):
    if after.bot:
        return
        
    old_status = str(before.status) if before else 'offline'
    new_status = str(after.status)

    if old_status != new_status:
        print(f'[ステータス] {after} が {new_status} になりました。', flush=True)
        send_to_web("presence", {
            "id": str(after.id),
            "status": new_status
        })

@client.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    old_channel = before.channel
    new_channel = after.channel
    
    # コンソール用ログ
    if old_channel is None and new_channel is not None:
        print(f'[通話] {member} が 🔊{new_channel.name} に参加しました。', flush=True)
    elif old_channel is not None and new_channel is None:
        print(f'[通話] {member} が 🔊{old_channel.name} から退出しました。', flush=True)
    elif old_channel is not None and new_channel is not None and old_channel.id != new_channel.id:
        print(f'[通話] {member} が 🔊{old_channel.name} から 🔊{new_channel.name} に移動しました。', flush=True)

    # Web画面用：ボイスチャンネルの入退室データを送信
    send_to_web("voice_update", {
        "member_id": str(member.id),
        "old_channel_id": str(old_channel.id) if old_channel else None,
        "new_channel_id": str(new_channel.id) if new_channel else None
    })

token = os.environ.get('DISCORD_TOKEN')
if token:
    client.run(token)
else:
    print("エラー: 環境変数 'DISCORD_TOKEN' が見つかりません。", flush=True)