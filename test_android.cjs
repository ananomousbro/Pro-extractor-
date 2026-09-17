const crypto = require('crypto');
const https = require('https');

function generateCwkey() {
    const key = Buffer.from('E12K7l97Z7wCo3Gu');
    const iv = Buffer.from('mOk15J2m12qZ2tKI');
    const msg = Date.now().toString() + "||crwillweb@4598";
    
    const blockSize = 16;
    const padLength = blockSize - (msg.length % blockSize);
    const padding = Buffer.alloc(padLength, padLength);
    const paddedMsg = Buffer.concat([Buffer.from(msg, 'utf8'), padding]);

    const cipher = crypto.createCipheriv('aes-128-cbc', key, iv);
    cipher.setAutoPadding(false);
    const enc = Buffer.concat([cipher.update(paddedMsg), cipher.final()]);
    return enc.toString('base64');
}

const cwkey = generateCwkey();

const data = JSON.stringify({
    deviceType: "android",
    password: "test",
    deviceModel: "Xiaomi M2007J20CI",
    deviceVersion: "Q(Android 10.0)",
    email: "7498987488",
    deviceIMEI: "d57adbd8a7b8u9i9",
    deviceToken: "fake_device_token"
});

const options = {
    hostname: 'elearn.crwilladmin.com',
    port: 443,
    path: '/api/v10/login-other',
    method: 'POST',
    headers: {
        "Host": "elearn.crwilladmin.com",
        "appver": "240",
        "apptype": "android",
        "cwkey": cwkey,
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/5.0.0-alpha.2"
    }
};

const req = https.request(options, res => {
    console.log(`statusCode: ${res.statusCode}`);
    res.on('data', d => {
        process.stdout.write(d);
    });
});
req.write(data);
req.end();
