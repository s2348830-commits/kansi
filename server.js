const http = require('http');
const { spawn } = require('child_process');

// Renderが割り当てるポート番号（デフォルトは3000）
const port = process.env.PORT || 3000;

// ダミーのWebサーバーを作成（cron-job.orgがここにアクセスします）
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Bot is awake and running!\n');
});

server.listen(port, () => {
    console.log(`Webサーバーがポート ${port} で起動しました。`);
    
    // Webサーバー起動後、PythonのBotプロセスを立ち上げる
    console.log('Discord Bot (bot.py) を起動しています...');
    const bot = spawn('python3', ['bot.py']);

    // Python側からの標準出力をNode.js側のコンソールに流す
    bot.stdout.on('data', (data) => {
        process.stdout.write(data.toString());
    });

    // Python側からのエラー出力をNode.js側のコンソールに流す
    bot.stderr.on('data', (data) => {
        process.stderr.write(data.toString());
    });

    bot.on('close', (code) => {
        console.log(`Botのプロセスが終了しました。コード: ${code}`);
    });
});