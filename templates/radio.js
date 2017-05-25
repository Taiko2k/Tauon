
var connect_fault = 5;
var index = -1;


function setArt(){

  $.getJSON("/radio/getpic",
      function(data) {
          index = data.index
          if (data.image != 'None'){
            $("#picture").attr('src', 'data:image/jpeg;base64,' + data.image)
          }
          else {
            $("#picture").attr('src', '#')
          }


          $('#title-text').text(data.artist + " - " + data.title)

      });
}


function update() {
            connect_fault = connect_fault - 1
            $.getJSON("/radio/update_radio",
                function(data) {
                    connect_fault = connect_fault + 1
                    $("#seekfront").width(Math.round(data.position * 700))

                    if (data.index != index){
                      setArt();
                    }
                });


        }

function tick(){

  update();
  if (connect_fault > 0) { setTimeout(tick, 5000); }
  else { alert("Connection lost, reload page to continue.")}
}

tick()
