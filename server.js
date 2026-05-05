const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const port = process.env.PORT || 3000;

// index.htmlやstyle.cssなどの静的ファイルを配信する
app.use(express.static(__dirname));

// サーバー内で保持しておく最新のDiscord状態
let cache = {
    guild_name: "Loading...",
    channels: [],
    members: [],
    messages: {} // チャンネルIDをキーにしてメッセージ配列を保存
};

// Webブラウザがアクセスしてきた時の処理
io.on('connection', (socket) => {
    console.log('Web画面が開かれました。');
    // 開いた瞬間に、現在保持しているサーバーの情報を送る
    socket.emit('init_state', cache);
});

server.listen(port, () => {
    console.log(`Webサーバーがポート ${port} で起動しました。`);
    
    // Pythonボットの起動
    const bot = spawn('python3', ['bot.py']);

    bot.stdout.on('data', (data) => {
        const lines = data.toString().split('\n');
        for (const line of lines) {
            if (!line.trim()) continue;
            
            try {
                // Pythonから送られたJSONデータを解析
                const payload = JSON.parse(line);
                handleBotEvent(payload);
            } catch (e) {
                // JSON以外の普通のprint出力（ログなど）はそのままコンソールへ
                console.log(line);
            }
        }
    });

    bot.stderr.on('data', (data) => {
        console.error("Bot Error:", data.toString());
    });
});

// Pythonから受け取ったデータをWeb画面に中継する関数
function handleBotEvent({ event, data }) {
    if (event === 'init') {
        cache.guild_name = data.guild_name;
        cache.channels = data.channels;
        cache.members = data.members;
        io.emit('init_state', cache);
    } 
    else if (event === 'message') {
        if (!cache.messages[data.channel_id]) {
            cache.messages[data.channel_id] = [];
        }
        cache.messages[data.channel_id].push(data);
        // メッセージ履歴が長くなりすぎないよう直近100件に制限
        if (cache.messages[data.channel_id].length > 100) {
            cache.messages[data.channel_id].shift();
        }
        io.emit('new_message', data);
    } 
    else if (event === 'presence') {
        const member = cache.members.find(m => m.id === data.id);
        if (member) {
            member.status = data.status;
        }
        io.emit('presence_update', data);
    }
}