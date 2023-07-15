
        $(document).ready(function() {
            $('#add-music-button').click(function() {
                // Open a file selection dialog when the button is clicked
                var fileInput = $('<input type="file" accept=".mp3,.ogg,.wav">');
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
                            //alert('Music added successfully!');
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
    $('#pause-music-button').click(function() {
        // Send a request to the server to stop the music
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
    var intervalId;
    var speed = 2;
    intervalId = setInterval(function() {
        updateTimers();
    }, 1000);

    function updateTimers() {
        $.get('/timer/value', function(data) {
            var timeLeft = parseInt(data);
            var timePlayed = 3600 - timeLeft
            var formattedTimeLeft = formatTime(timeLeft);
            var formattedTimePlayed = formatTime(timePlayed);
            $('#time-left').text(formattedTimeLeft);
            $('#time-played').text(formattedTimePlayed);
        });
    }

    function formatTime(seconds) {
        var minutes = Math.floor(seconds / 60);
        var remainingSeconds = seconds % 60;
        return minutes + ':' + (remainingSeconds < 10 ? '0' : '') + remainingSeconds.toFixed(0);
    }

    function updateSpeedDisplay() {
        var formattedSpeed = speed.toFixed(1);
        $('#speed-display').text('Timer Speed: ' + formattedSpeed + 'x');
    }

    function getTimerSpeed() {
        $.get('/timer/get-speed', function(data) {
            speed = parseFloat(data);
            updateSpeedDisplay();
        });
    }

    $('#start-game-button').click(function() {
        $.post('/timer/start', function(data) {
            console.log(data);
        }).done(function() {
        });
        intervalId = setInterval(function() {
            updateTimers();
        }, 1000);    
        $('#continue-button').hide();
        $('#pause-button').show();
    });

    $('#end-game-button').click(function() {
        clearInterval(intervalId);
        updateTimers();
        $.post('/timer/stop', function(data) {
            console.log(data);
        });
    });

    $('#speed-up-button').click(function() {
        $.post('/timer/speed', { change: 0.1 }, function(data) {
            speed += 0.1
            console.log(data);
            updateSpeedDisplay()
        });
    });
    
    $('#slow-down-button').click(function() {
        $.post('/timer/speed', { change: -0.1 }, function(data) {
            speed -= 0.1
            console.log(data);
            updateSpeedDisplay()
        });
    });

    $('#reset-button').click(function() {
        $.post('/timer/reset-speed', function(data) {
            console.log(data);
            speed = 1;
            updateSpeedDisplay();
        });
    });
    function updateButtonState(pauseState) {
        if (pauseState) {
            $('#pause-button').hide();
            $('#continue-button').show();
        } else {
            $('#pause-button').show();
            $('#continue-button').hide();
        }
    }
    function getButtonState() {
        $.get('/timer/pause-state', function(data) {
            var pauseState = (!data);
            updateButtonState(pauseState);
            console.log(data)
        });
    }

    $('#pause-button').click(function() {
        $.post('/timer/pause', function(data) {
            console.log(data);
            if (data === 'Timer paused') {
                $('#pause-button').hide();
                $('#continue-button').show();
            }
        });
    });

    $('#continue-button').click(function() {
        $.post('/timer/continue', function(data) {
            console.log(data);
            if (data === 'Timer continued') {
                $('#continue-button').hide();
                $('#pause-button').show();
            }
        });
    });
    

    function initializeTimer() {
        updateTimers();
        updateSpeedDisplay();
    }

    initializeTimer();
    getTimerSpeed();
    getButtonState();
});



function openMediaControlPage() {
    window.open('/media_control', '_blank', 'height=400,width=400');
}
$(document).ready(function() {
    $('#resume-music-button').click(function() {
        $.ajax({
            type: 'POST',
            url: '/resume_music',
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
    $('#stop-music-button').click(function() {
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
    $('#reboot-pi-mag').click(function() {
        $.ajax({
            type: 'POST',
            url: '/reboot-maglock-pi',
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