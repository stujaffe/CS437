document.onkeydown = updateKey;
document.onkeyup = resetKey;

var server_port = 8080;
var server_addr = "192.168.50.45";   // the IP address of your Raspberry PI


function client(){
    
    const net = require('net');
    var input = document.getElementById("message").value;

    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        // 'connect' listener.
        console.log('connected to server!');
        // send the message
        client.write(`${input}\r\n`);
    });
    
    // get the data from the server
    client.on('data', (data) => {
        const data_ret = data.toString().split("\n")
        temp = data_ret[0]
        speed = data_ret[1]
        power_supply = data_ret[2]

        document.getElementById("cpu_temperature").innerHTML = temp
        document.getElementById("speed").innerHTML = speed
        document.getElementById("power_supply").innerHTML = power_supply

        console.log(data.toString());
        client.end();
        client.destroy();
    });

    client.on('end', () => {
        console.log('disconnected from server');
    });


}

function send_data(input){
    const net = require('net');
 
    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        // 'connect' listener.
        console.log('connected to server!');
        // send the message
        client.write(`${input}`);
    });
}

// for detecting which key is been pressed w,a,s,d
function updateKey(e) {

    console.log(e.keyCode)

    e = e || window.event;

    if (e.keyCode == '87') {
        // up (w)
        document.getElementById("upArrow").style.color = "green";
        send_data("87");
    }
    else if (e.keyCode == '83') {
        // down (s)
        document.getElementById("downArrow").style.color = "green";
        send_data("83");
    }
    else if (e.keyCode == '65') {
        // left (a)
        document.getElementById("leftArrow").style.color = "green";
        send_data("65");
    }
    else if (e.keyCode == '68') {
        // right (d)
        document.getElementById("rightArrow").style.color = "green";
        send_data("68");
    }
    else if (e.keyCode == '88') {
        // stop the car (x)
        send_data("88")
    }
}

// reset the key to the start state 
function resetKey(e) {

    console.log(e.keyCode)

    e = e || window.event;

    document.getElementById("upArrow").style.color = "grey";
    document.getElementById("downArrow").style.color = "grey";
    document.getElementById("leftArrow").style.color = "grey";
    document.getElementById("rightArrow").style.color = "grey";
}


// update data for every 50ms
function update_data(){
    /*
    setInterval(function(){
        // get image from python server
        client();
    }, 50);
    */
    client()
}