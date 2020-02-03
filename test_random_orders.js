var http = require("http");

let options = {
    hostname: "localhost",
    port: 3000,
    path: "/api/neworder",
    method: "POST",
    headers: {
        "Accept-Language": "en-GB,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        // "Content-length": data.length,
        "Content-Language": "en-GB",
        "charset": "utf-8"
    }
}

function choose(choices) {
    var index = Math.floor(Math.random() * choices.length);
    return choices[index];
  }

function post() {
    alphabet = 'abcdefghijklmnopqrstuvwxyz'.split('');
    address = [101, 102, 103, 201, 202, 203]
    let name = choose(alphabet) + choose(alphabet) + choose(alphabet);
    let red = Math.ceil(Math.random() * 10);
    let blue = Math.ceil(Math.random() * 10);
    let green = Math.floor(Math.random() * 10);
    let add = choose(address);

    let data = `&customer=${name}&red=${red}&blue=${blue}&green=${green}&address=${add}`;

    let req = http.request(options, (res) => {
        res.on('data', (d) => {
            process.stdout.write(d);
            process.stdout.write('\n');
        });
    });
    req.on("error", (err) => {
        console.log(err);
    });
    req.write(data);
    req.end();
}

setInterval(() => {
    post();
}, 1000);