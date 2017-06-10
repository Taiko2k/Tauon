
var connect_fault = 5;
var index = -1;

$(".buttons li").click(function(){

  var buttonName = $(this).text()
  console.log("Button click: " + buttonName);

  $.post( "/remote/command", {
    cmd : buttonName
  });

  setTimeout(update, 100);

})

$("#seekback").click(function(e){
  console.log("Seek click: " + (e.pageX - $(this).offset().left));
  $("#seekfront").width(e.pageX - $(this).offset().left)
  $.post( "/remote/command", {
    cmd : "Seek " + ((e.pageX - $(this).offset().left) / 700 * 100)
  });


  setTimeout(update, 100);
})

function setArt(){

  $.getJSON("/remote/getpic",
      function(data) {
          index = data.index
          if (data.image != 'None'){
            $("#picture").attr('src', 'data:image/jpeg;base64,' + data.image)
          }
          else {
            $("#picture").attr('src', '#')
          }

          //$('#title-text').text(data.artist + " - " + data.title)

      });
}

function getPlayingTracks(){

  console.log("getTracks")
  $.getJSON("/remote/tl",
      function(data) {
          tracks = data.tracks;
          $("#tracklist").empty()
          for(i=0; i<tracks.length; i++){
            $(
                  '<div></div>'
                , {
                       text     : tracks[i][3] + ". " + tracks[i][1] + " - " + tracks[i][2]

                     , class    : 'track-entry'
                     , style    : ((tracks[i][0] === index) ? "color: #777; cursor: pointer" : "color: #444; cursor: pointer")
                     , id       : "jump" + tracks[i][0]
                     , appendTo : $("#tracklist")
                  })
          }
          $(".track-entry").click( function() {
            $.get("/remote/" + this.id)
            setTimeout(update, 200);
            });
      })


  }


function update() {
            connect_fault = connect_fault - 1
            $.getJSON("/remote/update",
                function(data) {
                    connect_fault = connect_fault + 1
                    $("#seekfront").width(Math.round(data.position * 700))

                    if (data.index != index){
                      setArt();
                      getPlayingTracks();
                    }
                });


        }

function tick(){

  update();
  if (connect_fault > 0) { setTimeout(tick, 5000); }
  else { alert("Connection lost, reload page to continue.")}
}

// console.log("getAlbums")
// $.getJSON("/remote/al",
//     function(data) {
//         tracks = data.tracks;
//         $("#tracklist").empty()
//         for(i=0; i<tracks.length; i++){
//           $(
//                 '<div></div>'
//               , {
//                      text     : tracks[i][1] + " - " + tracks[i][2]
//
//                    , class    : 'track-entry'
//                    , style    : ((tracks[i][3] === true) ? "color: #777; cursor: pointer" : "color: #444; cursor: pointer")
//                    , id       : "jump" + tracks[i][0]
//                    , appendTo : $("#albumlist")
//                 })
//         }
//         $(".track-entry").click( function() {
//           $.get("/remote/" + this.id)
//           setTimeout(update, 100);
//           });
//     })

tick()
