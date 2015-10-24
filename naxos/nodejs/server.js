'use strict';
const http = require('http');
const cookie_reader = require('cookie');
const querystring = require('querystring');

const NODE_PORT = process.env.NODE_PORT;
const HOST = process.env.NODE_HOST;
const HOST_PORT = process.env.NODE_HOST_PORT;
const DEBUG = true;

const app = http.createServer().listen(NODE_PORT);
const io = require('socket.io')(app);
const connected_users = {};

io.use(function(socket, next) {
    const handshakeData = socket.request;
    if(handshakeData.headers.cookie){
        next();
    }
    next(new Error('not authorized'));
});

io.on('connection', function(socket){
    const user = cookie_reader.parse(socket.request.headers.cookie).sessionid
    if (user in connected_users) {
        connected_users[user] += 1;
    } else {
        connected_users[user] = 1;
        if (DEBUG) console.log(user + ' connected');
        // Tell django the user has come online
        var data = querystring.stringify({
            sessionid: user,
            status: 'connected'
        });
        var options = {
            host: HOST,
            port: HOST_PORT,
            path: '/user/node_api/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': data.length
            }
        };
        var req = http.request(options, function(res){
            res.setEncoding('utf8');
            if (DEBUG) {
                res.on('data', function(chunk){
                    console.log("body: " + chunk)
                })
            }
        });
        req.write(data);
        req.end();
    };
    socket.on('disconnect', function(){
        setTimeout(function() {
            if (connected_users[user] === 1) {
                delete connected_users[user];
                if (DEBUG) {
                    console.log(user + ' disconnected');
                }
                // Tell django the user is now offline
                var data = querystring.stringify({
                    sessionid: user,
                    status: 'disconnected'
                })
                var options = {
                    host: HOST,
                    port: HOST_PORT,
                    path: '/user/node_api/',
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Content-Length': data.length
                    }
                }
                var req = http.request(options, function(res){
                    res.setEncoding('utf8');
                    if (DEBUG) {
                        res.on('data', function(chunk){
                            console.log("body: " + chunk)
                        })
                    }
                })
                req.write(data);
                req.end();
            } else {
                connected_users[user] -= 1;
            };
        }, 2 * 1000);
    });
})
