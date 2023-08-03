
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
      url: 'http://192.168.0.104:5000/maglock/status/' + maglockNumber,
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
    $('#reboot-pi-music').click(function() {
        $.ajax({
            type: 'POST',
            url: '/reboot-music-pi',
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#backup-top-pi').click(function() {
        $.ajax({
            type: 'POST',
            url: '/backup-top-pi',
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    $('#backup-middle-pi').click(function() {
        $.ajax({
            type: 'POST',
            url: '/backup-middle-pi',
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

$(document).ready(function() {
    function updateStatusDisplay() {
        $.get('/get_file_status', function(data) {
            $('#status-display').empty();

            const playingSongs = data.filter(entry => entry.status === 'playing');
            const pausedSongs = data.filter(entry => entry.status === 'paused');

            if (playingSongs.length > 0) {
                $('#music-list').empty();

                playingSongs.forEach(entry => {
                    const { filename, soundcard_channel } = entry;
                    $('#status-display').append(`<div>${filename} is playing!</div>`);
                    $('#music-list').append(`
                        <li>
                            ${filename}
                            <button class="pause-button" data-file="${filename}" data-channel="${soundcard_channel}">Pause</button>
                            <button class="resume-button" data-file="${filename}" data-channel="${soundcard_channel}">Resume</button>
                        </li>
                    `);
                });
            } else {
                $('#music-list').empty(); // Clear the list if there are no songs playing
            }

            if (pausedSongs.length > 0) {
                $('#status-display').append('<div>Paused songs:</div>');
                pausedSongs.forEach(entry => {
                    const { filename, soundcard_channel } = entry;
                    $('#status-display').append(`<div>${filename} is paused!</div>`);
                    $('#music-list').append(`
                        <li>
                            ${filename}
                            <button class="resume-button" data-file="${filename}" data-channel="${soundcard_channel}">Resume</button>
                        </li>
                    `);
                });
            }
        });
    }
    


    // Handle pause button click
    $(document).on('click', '.pause-button', function() {
        const selectedFile = $(this).data('file');
        const selectedChannel = $(this).data('channel');
        $.ajax({
            type: 'POST',
            url: '/pause_music',
            data: { file: selectedFile, channel: selectedChannel },
            success: function(response) {
                console.log(response);
                updateStatusDisplay(); // Update the status display after pausing the song
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    
    

    // Handle resume button click
    $(document).on('click', '.resume-button', function() {
        const selectedFile = $(this).data('file');
        const selectedChannel = $(this).data('channel');
        $.ajax({
            type: 'POST',
            url: '/resume_music',
            data: { file: selectedFile, channel: selectedChannel },
            success: function(response) {
                console.log(response);
                updateStatusDisplay(); // Update the status display after resuming the song
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
    
    

    // Call the function initially and update the status display every 5 seconds
    updateStatusDisplay();
    setInterval(updateStatusDisplay, 5000);
});
function updatePiStatus() {
    $.ajax({
        url: '/get-pi-status',
        method: 'GET',
        success: function(data) {
            // Update the table with the latest status data
            $('#status-table').html(data);
        },
        complete: function() {
            // Schedule the next update after 5 seconds
            setTimeout(updatePiStatus, 5000);
        }
    });
}

// Start updating status on page load
$(document).ready(function() {
    updatePiStatus();
});