
var connect_fault = 5;
var index = -1;
var status = 0;
var sound = document.createElement('audio');
sound.id       = 'audio-player';
sound.controls = 'controls';
sound.type     = 'audio/ogg';
sound.preload  = 'none';

var request = new XMLHttpRequest();

function setArt(){

    request.open('GET', '/radio/getpic', true);
    request.onload = function() {

        var data = JSON.parse(this.response);

        index = data.index
        if (data.image != 'None'){
            document.getElementById("picture").src = 'data:image/jpeg;base64,' + data.image
        }
        else {
             document.getElementById("picture").src = '#'
        }

        document.getElementById("title-text").innerText = data.artist + " - " + data.title
        document.getElementById("lyrics").innerHTML = data.lyrics

      };

    request.send();
}

function update() {
    connect_fault = connect_fault - 1
    request.open('GET', '/radio/update_radio', true);
    request.onload = function() {
        var data = JSON.parse(this.response);

        connect_fault = connect_fault + 1
        document.getElementById('seekfront').style.width = Math.round(data.position * 700) + "px";

        if (data.index != index){
          setArt();
        }

        if (status == 1 && data.index == -1) {
            // The stream has stopped
            status = 2;
            sound.src = "";
            sound.load();
        }

        if (status == 2 && data.index > -1){
            // Stream starts again
            status = 1;
            sound.src = "http://" + window.location.hostname + ":" + data.port;

        }

        if (status == 0 && data.index > -1) {
            // Show player for the first time when stream starts
            status = 1;
            sound.src = "http://" + window.location.hostname + ":" + data.port;
            document.getElementById('player').appendChild(sound);
        }
        };

    request.send();
}

function tick(){

  update();
  if (connect_fault > 0) { setTimeout(tick, 5000); }
  else { alert("Connection lost, reload page to continue.")}
}

tick()
