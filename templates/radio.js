
var connect_fault = 5;
var index = -1;
var status = 0;
var port = 8000;
var sound = document.createElement('audio');
sound.id       = 'audio-player';
//sound.controls = 'controls';
sound.type     = 'audio/ogg';
sound.preload  = 'none';

document.getElementById('player').appendChild(sound);

vol_slider = document.getElementById('vol-slider')

function volChange(){
    sound.volume = vol_slider.value / 100;
}

vol_slider.addEventListener('input', volChange, false);

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

        connect_fault = 2;
        port = data.port;
        document.getElementById('seekfront').style.width = Math.round(data.position * 700) + "px";

        if (data.index != index){
          setArt();
        }

        if (status > 0){
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
                sound.load();
                sound.play();
                console.log("AUTO RESUME");
            }
        }

    };

    request.send();
}

var playbutton = document.getElementById("play-button");
playbutton.onclick = function() {
    if (status == 0){
        document.getElementById("play-icon").style.display = "none"
        document.getElementById("stop-icon").style.display = "block"
        if (index == -1) {
            status = 2;
        }
        else {
            sound.src = "http://" + window.location.hostname + ":" + port;
            sound.load();
            sound.play();
            console.log("PRESS PLAY");
            status = 1;
         }
    }
    else {
        document.getElementById("play-icon").style.display = "block"
        document.getElementById("stop-icon").style.display = "none"
        status = 0;
        sound.src = "";
        sound.load();
        console.log("PRESS PAUSE");
    }
}

function tick(){

  update();
  if (connect_fault > 0) {
    setTimeout(tick, 5000);
  }
  else {
     document.getElementById("picture").src = '#';
     document.getElementById("title-text").innerText = "-- Connection Lost --";
     document.getElementById("lyrics").innerHTML = "";
    if (status == 1) {
        status = 2;
        sound.src = "";
        sound.load();
    }

    setTimeout(tick, 15000);
   }
}

tick()
