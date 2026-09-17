const crypto = require('crypto');
const https = require('https');

function generateCwkey() {
    const key = Buffer.from('E12K7l97Z7wCo3Gu');
    const iv = Buffer.from('mOk15J2m12qZ2tKI');
    const msg = Date.now().toString() + "||crwillweb@4598";
    
    // PKCS7 padding
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
console.log("Generated cwkey:", cwkey);

const data = JSON.stringify({
    deviceType: "web",
    pwd: "Suraj@123",
    deviceModel: "ChromeCDM",
    deviceVersion: "152.0.0.0",
    userid: "7498987488",
    deviceIMEI: "d1a5b3b4-d6f7-4998-8cdb-81bb1c3ed6b7-5a487141-e89a-4ad5-9d72-b031b3e80340-07046ee9-9885-4882-8b90-de6904db0dff"
});

const options = {
    hostname: 'wbspec.crwilladmin.com',
    port: 443,
    path: '/api/v1/login',
    method: 'POST',
    headers: {
        "Host": "wbspec.crwilladmin.com",
        "appver": "1",
        "apptype": "web",
        "cwkey": cwkey,
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "origin": "https://web.careerwill.com",
        "referer": "https://web.careerwill.com/"
    }
};

const req = https.request(options, res => {
    console.log(`statusCode: ${res.statusCode}`);
    res.on('data', d => {
        process.stdout.write(d);
    });
});

req.on('error', error => {
    console.error(error);
});

req.write(data);
req.end();
