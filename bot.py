import discord
import os

# 必要な権限（Intents）の設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容の取得
intents.presences = True        # オンライン状態の取得
intents.members = True          # メンバー情報の取得
intents.voice_states = True     # ボイスチャンネル状態の取得

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'起動完了！ {client.user} としてログインしました。')
    print('--- 監視を開始します ---')

# 1. テキストチャンネルのメッセージ監視
@client.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return
    print(f'[メッセージ] チャンネル: #{message.channel.name} | ユーザー: {message.author} | 内容: {message.content}')

# 2. ユーザーのオンライン/オフライン状態の監視
@client.event
async def on_presence_update(before, after):
    if after.bot:
        return
    
    # 以前のステータスと現在のステータス（文字列化して取得）
    old_status = str(before.status) if before else 'offline'
    new_status = str(after.status)

    if old_status != new_status:
        print(f'[ステータス] ユーザー: {after} が {old_status} から {new_status} になりました。')

# 3. ボイスチャンネルの入退室監視
@client.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    old_channel = before.channel
    new_channel = after.channel

    if old_channel is None and new_channel is not None:
        print(f'[通話] ユーザー: {member} が 🔊{new_channel.name} に参加しました。')
    elif old_channel is not None and new_channel is None:
        print(f'[通話] ユーザー: {member} が 🔊{old_channel.name} から退出しました。')
    elif old_channel is not None and new_channel is not None and old_channel.id != new_channel.id:
        print(f'[通話] ユーザー: {member} が 🔊{old_channel.name} から 🔊{new_channel.name} に移動しました。')

# Renderで設定した環境変数からトークンを取得して起動
token = os.environ.get('DISCORD_TOKEN')
if token:
    client.run(token)
else:
    print("エラー: 環境変数 'DISCORD_TOKEN' が見つかりません。Renderで設定してください。")