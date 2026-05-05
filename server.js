const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const port = process.env.PORT || 3000;

app.use(express.static(__dirname));

let cache = {
    guild_name: "Loading...",
    channels: [],
    voice_channels: [], // 追加
    members: [],
    messages: {} 
};

io.on('connection', (socket) => {
    console.log('Web画面が開かれました。');
    socket.emit('init_state', cache);
});

server.listen(port, () => {
    console.log(`Webサーバーがポート ${port} で起動しました。`);
    
    const bot = spawn('python3', ['bot.py']);

    bot.stdout.on('data', (data) => {
        const lines = data.toString().split('\n');
        for (const line of lines) {
            if (!line.trim()) continue;
            
            try {
                const payload = JSON.parse(line);
                handleBotEvent(payload);
            } catch (e) {
                console.log(line);
            }
        }
    });

    bot.stderr.on('data', (data) => {
        console.error("Bot Error:", data.toString());
    });
});

function handleBotEvent({ event, data }) {
    if (event === 'init') {
        cache.guild_name = data.guild_name;
        cache.channels = data.channels;
        cache.voice_channels = data.voice_channels || []; // 追加
        cache.members = data.members;
        io.emit('init_state', cache);
    } 
    else if (event === 'message') {
        if (!cache.messages[data.channel_id]) {
            cache.messages[data.channel_id] = [];
        }
        cache.messages[data.channel_id].push(data);
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
    // 追加：通話の入退室イベントを処理
    else if (event === 'voice_update') {
        const { member_id, old_channel_id, new_channel_id } = data;
        
        // 前のチャンネルからメンバーを削除
        if (old_channel_id) {
            const oldVc = cache.voice_channels.find(vc => vc.id === old_channel_id);
            if (oldVc) {
                oldVc.members = oldVc.members.filter(id => id !== member_id);
            }
        }
        // 新しいチャンネルにメンバーを追加
        if (new_channel_id) {
            const newVc = cache.voice_channels.find(vc => vc.id === new_channel_id);
            if (newVc && !newVc.members.includes(member_id)) {
                newVc.members.push(member_id);
            }
        }
        // ブラウザに更新を通知
        io.emit('voice_update', data);
    }
}