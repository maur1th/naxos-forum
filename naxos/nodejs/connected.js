var http = require('http');
var app= http.createServer();
var io = require('socket.io')(app);
var cookie_reader = require('cookie');
var querystring = require('querystring');

app.listen(4000);

io.use(function(socket, next) {
    var handshakeData = socket.request;
    if(handshakeData.headers.cookie){
        next();
    }
    next(new Error('not authorized'));
});

var connected_users = {};
io.on('connection', function(socket){
    var user = cookie_reader.parse(socket.request.headers.cookie).sessionid
    if (user in connected_users) {
        connected_users[user] += 1;
    } else {
        connected_users[user] = 1;
        console.log(user + ' connected');
        // Tell django the user has come online
        var data = querystring.stringify({
            sessionid: user,
            status: 'connected'
        });
        var options = {
            host:'geekattitude.org',
            port: 80,
            path: '/user/node_api/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': data.length
            }
        };
        var req = http.request(options, function(res){
            res.setEncoding('utf8');
            res.on('data', function(chunk){
                console.log("body: " + chunk)
            })
        });
        req.write(data);
        req.end();
    };
    socket.on('disconnect', function(){
        setTimeout(function() {
            if (connected_users[user] === 1) {
                delete connected_users[user];
                console.log(user + ' disconnected');
                // Tell django the user is now offline
                var data = querystring.stringify({
                    sessionid: user,
                    status: 'disconnected'
                })
                var options = {
                    host:'geekattitude.org',
                    port: 80,
                    path: '/user/node_api/',
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Content-Length': data.length
                    }
                }
                var req = http.request(options, function(res){
                    res.setEncoding('utf8');
                    res.on('data', function(chunk){
                        console.log("body: " + chunk)
                    })
                })
                req.write(data);
                req.end();
            } else {
                connected_users[user] -= 1;
            };
        }, 2 * 1000);
    });
})
