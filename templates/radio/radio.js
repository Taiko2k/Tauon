

var connect_fault = 5;
//var index = -1;
var local_status = 0;
var local_id = "";
var local_duration = 0;
var play = false;

var sound = document.createElement("audio");
sound.id = "audio-player";
//sound.controls = 'controls';
sound.type = "audio/ogg";
sound.preload = "none";
sound.volume = 0.85;

document.getElementById("player").appendChild(sound);

vol_slider = document.getElementById("vol-slider");

function volChange() {
    sound.volume = vol_slider.value / 100;
}

vol_slider.addEventListener("input", volChange, false);

var request = new XMLHttpRequest();

function setArt(id) {
    request.open("GET", "/llapi/picture/" + id, true);
    request.onload = function () {
        var data = JSON.parse(this.response);
        if (data.image_data != "None") {
            document.getElementById("picture").src = "data:image/jpeg;base64," + data.image_data;
        } else {
            document.getElementById("picture").src = "/radio/logo-bg.png";
        }

        // document.getElementById("title-text").innerText = data.title;
        // document.getElementById("album-text").innerText = data.album;
        // document.getElementById("artist-text").innerText = data.artist;
        // document.getElementById("lyrics").innerHTML = data.lyrics;
    };

    request.send();
}

function update() {
    console.log("Update");
    connect_fault = connect_fault - 1;
    request.open("GET", "/llapi/poll", true);
    request.onload = function () {
        var data = JSON.parse(this.response);
    //     connect_fault = 2;
        console.log(data.id);
        document.getElementById("seekfront").style.width = Math.round((data.position / data.duration) * 100) + "%";

    //     if (data.index != index) {
    //         setArt();
    //     }
        if (data.status == 0){
            console.log("Idle");
            if (local_status != 0){
                local_status = 0;
                document.getElementById("picture").src = "/radio/logo-bg.png";
                document.getElementById("artist-text").innerText = "";
                document.getElementById("title-text").innerText = "";
            }

            if (!sound.paused){
                sound.pause();
            }
            return;
        }

        // the track has switched?
        if (data.id != local_id && local_status == 1){
            local_status = -1;
            // if (2 < local_duration - sound.currentTime < 4){
            //     console.log("Close to finish!");
            //     return
            // }

        } else {
            if (Math.abs(sound.currentTime - data.position) > 12){
                console.log("seek")
                sound.currentTime = data.position;
            }
        }
        if (local_status == 1 && data.status == 2){
            local_status = 2;
            sound.pause();
            return;
        }
        if (local_status == 2 && data.status == 1){
            sound.play();
            local_status = 1;
            return;
        }

        if (local_status != data.status){
            if (data.status == 1){
                console.log("go start");
                sound.src = "/llapi/audiofile/" + data.id;
                if (data.position < 6){
                    sound.currentTime = 0;
                } else {
                    sound.currentTime = data.position;
                }
                if (play){
                    sound.load();
                    sound.play();
                }
                local_status = 1;
                local_id = data.id;
                local_duration = data.duration;

                document.getElementById("title-text").innerText = data.title;
                document.getElementById("artist-text").innerText = data.artist;
                setArt(data.id);


            } else if (data.status == 0) {
                console.log("go stop");
                local_status = 0;
                sound.pause();
                document.getElementById("picture").src = "/radio/logo-bg.png";
            }

        }
    }

    request.onerror = function () {
        local_status = 0;
        document.getElementById("picture").src = "/radio/logo-bg.png";
        document.getElementById("artist-text").innerText = "";
        document.getElementById("title-text").innerText = "";
        if (!sound.paused){
            sound.pause();
        }
    }

    request.send();
}

var playbutton = document.getElementById("play-button");
playbutton.onclick = function () {
    if (!play) {
        play = true;
        document.getElementById("play-icon").style.display = "none";
        document.getElementById("stop-icon").style.display = "block";
        local_status = -1;
    } else {
        play = false;
        sound.pause();
        document.getElementById("play-icon").style.display = "block";
        document.getElementById("stop-icon").style.display = "none";      
    }


};

function tick() {
    console.log("TICK");
    update();
    setTimeout(tick, 2500);
    // if (connect_fault > 0) {
    //     
    //     console.log("A");
    // } else {
    //     console.log("CONNECTION LOST");
    //     // document.getElementById("picture").src = "/radio/logo-bg.png";
    //     // document.getElementById("title-text").innerText = "-- Server Offline --";
    //     // document.getElementById("artist-text").innerText = "";
    //     // document.getElementById("lyrics").innerHTML = "";
    //     // if (status == 1) {
    //     //     status = 2;
    //     //     sound.src = "";
    //     //     sound.load();
    //     // }
    //     setTimeout(tick, 15000);
    // }
}

tick();
