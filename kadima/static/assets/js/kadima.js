function startTime() {
    var today = new Date();
    var year = today.getFullYear()
    var month = today.getMonth()
    var day = today.getDate()
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();
    m = checkTime(m);
    s = checkTime(s);

    document.getElementById('date').innerHTML = 
    day + "/" + month + "/" + year;

    document.getElementById('clock').innerHTML =
    h + ":" + m + ":" + s;
    var t = setTimeout(startTime, 500);
  }
  function checkTime(i) {
    if (i < 10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
  }


  $(document).ready(function(){
      setTimeout(function() {
              // $(".display-message").hide('blind', {}, 300)
        $(".display-message").hide();
      }, 5000);
  });

  var up = document.getElementById("up_sound"); 
  var down = document.getElementById("down_sound"); 
  
  function playUpAudio() { 
    up.play(); 
  } 

  function playDownAudio() { 
      down.play(); 
  } 

// Sorting table
// $(document).ready(function () {
// $('#stocksTable').DataTable({
// "ordering": true // false to disable sorting (or any other option)
// });
// $('.dataTables_length').addClass('bs-select');
// });