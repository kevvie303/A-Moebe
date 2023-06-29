
        $(document).ready(function() {
            $('#add-music-button').click(function() {
                // Open a file selection dialog when the button is clicked
                var fileInput = $('<input type="file">');
                fileInput.on('change', function() {
                    var file = fileInput[0].files[0];
                    // Send the selected file to the server
                    var formData = new FormData();
                    formData.append('file', file);
                    $.ajax({
                        type: 'POST',
                        url: '/add_music',
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(response) {
                            console.log(response);
                            alert('Music added successfully!');
                        },
                        error: function(error) {
                            console.log(error);
                            alert('Failed to add music.');
                        }
                    });
                });
                fileInput.click(); // Trigger the file selection dialog
            });
        });
    
    
$(document).ready(function() {
    // ...

    $('#select-file-button').click(function() {
        // Open a new window with the file selection page
        var fileSelectionWindow = window.open('/file_selection', '_blank', 'height=400,width=400');

        // Poll for the selected file
        var pollTimer = setInterval(function() {
            if (fileSelectionWindow.closed) {
                clearInterval(pollTimer);
            } else {
                try {
                    var selectedFile = fileSelectionWindow.selectedFile;
                    if (selectedFile) {
                        // Send the selected file to the server
                        $.ajax({
                            type: 'POST',
                            url: '/play_music',
                            data: {file: selectedFile},
                            success: function(response) {
                                console.log(response);
                            },
                            error: function(error) {
                                console.log(error);
                            }
                        });
                        clearInterval(pollTimer);
                    }
                } catch (error) {
                    // Ignore any errors when accessing selectedFile property
                }
            }
        }, 1000); // Adjust the interval as needed
    });
    $('#stop-music-button').click(function() {
        // Send a request to the server to stop the music
        $.ajax({
            type: 'POST',
            url: '/stop_music',
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});
    
    
        $(document).ready(function() {
            // Handle turn on button click
            $('.turn-on-button').click(function() {
                var maglock = $(this).data('maglock');
                $.ajax({
                    type: 'POST',
                    url: '/turn_on',
                    data: {maglock: maglock},
                    success: function(response) {
                        console.log(response);
                    },
                    error: function(error) {
                        console.log(error);
                    }
                });
            });

            // Handle turn off button click
            $('.turn-off-button').click(function() {
                var maglock = $(this).data('maglock');
                $.ajax({
                    type: 'POST',
                    url: '/turn_off',
                    data: {maglock: maglock},
                    success: function(response) {
                        console.log(response);
                    },
                    error: function(error) {
                        console.log(error);
                    }
                });
            });
        });
    

$(document).ready(function() {
  function updateMaglockStatus(maglockNumber) {
    $.ajax({
      type: 'GET',
      url: 'http://192.168.1.19:5000/maglock/status/' + maglockNumber,
      success: function(response) {
        var maglockStatus = response.status;
        var maglockStatusText = maglockStatus === 'locked' ? 'Locked' : 'Unlocked';

        if (maglockNumber === 1) {
          $('#maglock1-status').text(maglockStatusText);
        } else if (maglockNumber === 2) {
          $('#maglock2-status').text(maglockStatusText);
        }
      },
      error: function(error) {
        console.log(error);
      }
    });
  }

  // Update maglock status on page load
  updateMaglockStatus(1);
  updateMaglockStatus(2);

    // Update maglock statuses periodically
    setInterval(function() {
        updateMaglockStatus(1);
        updateMaglockStatus(2);
    }, 500); // Update every 2 seconds
});

    
        $(document).ready(function() {
            var timePlayed = 0;
            var timeLeft = 3600; // 60 minutes in seconds
            var intervalId;
            var speed = 1;

            function updateTimers() {
                var formattedTimePlayed = formatTime(timePlayed);
                var formattedTimeLeft = formatTime(timeLeft);

                $('#time-played').text(formattedTimePlayed);
                $('#time-left').text(formattedTimeLeft);
            }

            function formatTime(seconds) {
                var minutes = Math.floor(seconds / 60);
                var remainingSeconds = seconds % 60;
                return minutes + ':' + (remainingSeconds < 10 ? '0' : '') + remainingSeconds.toFixed(0);
            }

            function updateSpeedDisplay() {
                $('#speed-display').text('Timer Speed: ' + speed + 'x');
            }

            $('#start-game-button').click(function() {
                        // Add an AJAX request to trigger the command on the server side
            //     $.ajax({
            //         type: 'POST',
            //         url: '/play_music',
            //     success: function(response) {
            //         console.log(response);
            //     },
            //     error: function(error) {
            //         console.log(error);
            //     }
            // });
                intervalId = setInterval(function() {
                    timePlayed++;
                    timeLeft = Math.max(0, timeLeft - speed);
                    updateTimers();
                }, 1000);
            });

            $('#speed-up-button').click(function() {
                speed += 0.1;
                updateSpeedDisplay();
            });

            $('#slow-down-button').click(function() {
                speed -= 0.1;
                updateSpeedDisplay();
            });

            $('#reset-button').click(function() {
                // $.ajax({
                //     type: 'POST',
                //     url: '/pause_music',
                //     success: function(response) {
                //         console.log(response);
                //     },
                //     error: function(error) {
                //         console.log(error);
                //     }
                // });
                speed = 1;
                updateSpeedDisplay();
            });
            var gameEnded = false; // Track if game is already ended

            // Handle end game button click
            $('#end-game-button').click(function() {
                if (!gameEnded) {
                    clearInterval(intervalId); // Stop the timer
                    gameEnded = true; // Set game ended flag
                } else {
                    timePlayed = 0; // Reset the time played
                    timeLeft = 3600; // Reset the time left to 60 minutes
                    updateTimers(); // Update the displayed timers
                    gameEnded = false; // Reset game ended flag
                }
            });
        });
function openMediaControlPage() {
    window.open('/media_control', '_blank', 'height=400,width=400');
}
$(document).ready(function() {
    $('#pause-music-button').click(function() {
        $.ajax({
            type: 'POST',
            url: '/pause_music',
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});

function updateState() {
    $.ajax({
        url: "/get_state", // Endpoint in your app.py to fetch the state
        type: "GET",
        success: function(response) {
            var state = response.state;
            $("#current-state").text("Walkman: " + state);
        },
        error: function() {
            $("#current-state").text("Walkman: unknown");
        }
    });
}

// Update the state every 5 seconds (5000 milliseconds)
setInterval(updateState, 5000);