$(document).ready(function () {
  $("#add-music-button1").click(function () {
    // Open a file selection dialog when the button is clicked
    var fileInput = $('<input type="file" accept=".mp3,.ogg,.wav">');
    fileInput.on("change", function () {
      var file = fileInput[0].files[0];
      // Send the selected file to the server
      var formData = new FormData();
      formData.append("file", file);
      $.ajax({
        type: "POST",
        url: "/add_music1",
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
          console.log(response);
          //alert('Music added successfully!');
        },
        error: function (error) {
          console.log(error);
          alert("Failed to add music.");
        },
      });
    });
    fileInput.click(); // Trigger the file selection dialog
  });
});
$(document).ready(function () {
  $("#add-music-button2").click(function () {
    // Open a file selection dialog when the button is clicked
    var fileInput = $('<input type="file" accept=".mp3,.ogg,.wav">');
    fileInput.on("change", function () {
      var file = fileInput[0].files[0];
      // Send the selected file to the server
      var formData = new FormData();
      formData.append("file", file);
      $.ajax({
        type: "POST",
        url: "/add_music2",
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
          console.log(response);
          //alert('Music added successfully!');
        },
        error: function (error) {
          console.log(error);
          alert("Failed to add music.");
        },
      });
    });
    fileInput.click(); // Trigger the file selection dialog
  });
});

$(document).ready(function () {
  // ...

  $("#select-file-button").click(function () {
    // Open a new window with the file selection page
    var fileSelectionWindow = window.open(
      "/file_selection",
      "_blank",
      "height=400,width=400"
    );

    // Poll for the selected file
    var pollTimer = setInterval(function () {
      if (fileSelectionWindow.closed) {
        clearInterval(pollTimer);
      } else {
        try {
          var selectedFile = fileSelectionWindow.selectedFile;
          if (selectedFile) {
            // Send the selected file to the server
            $.ajax({
              type: "POST",
              url: "/play_music",
              data: { file: selectedFile },
              success: function (response) {
                console.log(response);
              },
              error: function (error) {
                console.log(error);
              },
            });
            clearInterval(pollTimer);
          }
        } catch (error) {
          // Ignore any errors when accessing selectedFile property
        }
      }
    }, 1000); // Adjust the interval as needed
  });
  $("#pause-music-button").click(function () {
    // Send a request to the server to stop the music
    $.ajax({
      type: "POST",
      url: "/pause_music",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
});

$(document).ready(function () {
  // Handle button click for both turning on and off
  $(".lock-buttons button").click(function () {
    var maglockName = $(this).closest(".lock").find("p").text();
    var action = $(this).hasClass("turn-on-button") ? "locked" : "unlocked";

    $.ajax({
      type: "POST",
      url: "/control_maglock",
      data: { maglock: maglockName, action: action },
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
});

$(document).ready(function () {
  function updateMaglockStatus(maglockNumber, maglockName, maglockURL) {
    $.ajax({
      type: "GET",
      url: `${maglockURL}/maglock/status/${maglockNumber}`,
      success: function (response) {
        var maglockStatus = response.status;
        var maglockStatusText =
          maglockStatus === "locked" ? "Locked" : "Unlocked";

        // Create or update the maglock status element
        var maglockStatusElement = $(`#maglock${maglockNumber}-status`);
        if (maglockStatusElement.length) {
          maglockStatusElement.html(
            `${maglockName}: <strong>${maglockStatusText}</strong>`
          );
        } else {
          var newMaglockStatusElement = $("<p>").html(
            `${maglockName}: <strong>${maglockStatusText}</strong>`
          );
          newMaglockStatusElement.attr("id", `maglock${maglockNumber}-status`);
          $("#maglock-status-container").append(newMaglockStatusElement);
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }

  function updateAllMaglockStatuses(maglockURL) {
    $.ajax({
      type: "GET",
      url: `${maglockURL}/maglock/list`,
      success: function (response) {
        var maglocks = response.maglocks;

        for (var i = 0; i < maglocks.length; i++) {
          var maglock = maglocks[i];
          updateMaglockStatus(maglock.number, maglock.name, maglockURL);
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }

  // Initial update for maglocks from the URL where you list them
  updateAllMaglockStatuses("http://192.168.0.104:5000");
  updateAllMaglockStatuses("http://192.168.0.114:5001");

  // Update maglock statuses periodically
  setInterval(function () {
    updateAllMaglockStatuses("http://192.168.0.104:5000");
    updateAllMaglockStatuses("http://192.168.0.114:5001");
  }, 500); // Update every 2 seconds
});

$(document).ready(function () {
  // Create an object to store the latest sensor statuses
  var latestSensorStatuses = {};

  // Function to update sensor status
  function updateSensorStatus(sensorNumber, sensorName, sensorURL) {
    $.ajax({
      type: "GET",
      url: `${sensorURL}/sensor/status/${sensorNumber}`,
      success: function (response) {
        var sensorStatus = response.status;

        // Check if the status has changed
        if (latestSensorStatuses[sensorNumber] !== sensorStatus) {
          // Store the latest sensor status in the object
          latestSensorStatuses[sensorNumber] = sensorStatus;

          // Create or update the sensor status element
          var sensorStatusElement = $(`#sensor${sensorNumber}-status`);
          if (sensorStatusElement.length) {
            sensorStatusElement.html(
              sensorName + ": <strong>" + sensorStatus + "</strong>"
            );
          } else {
            var newSensorStatusElement = $("<p>").html(
              sensorName + ": <strong>" + sensorStatus + "</strong>"
            );
            newSensorStatusElement.attr("id", `sensor${sensorNumber}-status`);
            $("#sensor-status-container").append(newSensorStatusElement);
          }
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }

  // Function to update all sensor statuses
  function updateAllSensorStatuses(sensorURL) {
    $.ajax({
      type: "GET",
      url: `${sensorURL}/sensor/list`,
      success: function (response) {
        var sensors = response.sensors;

        for (var sensorNumber in sensors) {
          var sensorName = sensors[sensorNumber];
          updateSensorStatus(sensorNumber, sensorName, sensorURL);
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }
  function updateLastKeypadCode(sensorURL) {
    $.ajax({
      type: "GET",
      url: `${sensorURL}/keypad/pressed_keys`,
      success: function (response) {
        var pressedKeysArrays = response.pressed_keys_arrays;
        if (pressedKeysArrays.length > 0) {
          // Get the last-used code from the array
          var lastUsedCodeArray =
            pressedKeysArrays[pressedKeysArrays.length - 1];
          var lastUsedCode = lastUsedCodeArray.join(""); // Combine keys into a single code
          $("#keypad-shed-code strong").text(lastUsedCode);
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }

  // Initial update for normal sensors from the first URL
  updateAllSensorStatuses("http://192.168.0.104:5000");
  updateLastKeypadCode("http://192.168.0.104:5000");
  // Initial update for IR sensors from the second URL
  updateAllSensorStatuses("http://192.168.0.105:5001");

  // Function to update IR sensor status
  function updateIRSensorStatus(sensorNumber, sensorName, sensorURL) {
    $.ajax({
      type: "GET",
      url: `${sensorURL}/ir-sensor/status/${sensorNumber}`,
      success: function (response) {
        var irSensorStatus = response.status;

        // Check if the status has changed
        if (latestSensorStatuses[sensorNumber] !== irSensorStatus) {
          // Create or update the IR sensor status element
          var irSensorStatusElement = $(`#ir-sensor${sensorNumber}-status`);
          if (irSensorStatusElement.length) {
            irSensorStatusElement.html(
              sensorName + ": <strong>" + irSensorStatus + "</strong>"
            );
          } else {
            var newIrSensorStatusElement = $("<p>").html(
              sensorName + ": <strong>" + irSensorStatus + "</strong>"
            );
            newIrSensorStatusElement.attr(
              "id",
              `ir-sensor${sensorNumber}-status`
            );
            $("#ir-sensor-status-container").append(newIrSensorStatusElement);
          }
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }

  // Function to update all IR sensor statuses
  function updateAllIRSensorStatuses(sensorURL) {
    $.ajax({
      type: "GET",
      url: `${sensorURL}/ir-sensor/list`,
      success: function (response) {
        var irSensors = response.sensors;

        for (var i = 0; i < irSensors.length; i++) {
          var sensor = irSensors[i];
          updateIRSensorStatus(sensor.number, sensor.name, sensorURL);
        }
      },
      error: function (error) {
        console.log(error);
      },
    });
  }

  // Initial update for IR sensors from the second URL
  updateAllIRSensorStatuses("http://192.168.0.114:5001");

  // Update normal sensor statuses periodically
  setInterval(function () {
    updateAllSensorStatuses("http://192.168.0.104:5000");
    updateAllSensorStatuses("http://192.168.0.105:5001");
    updateLastKeypadCode("http://192.168.0.104:5000");
  }, 500);

  // Update IR sensor statuses periodically
  setInterval(function () {
    updateAllIRSensorStatuses("http://192.168.0.114:5001");
  }, 500);
});

$(document).ready(function () {
  var intervalId;
  var speed = 2;
  intervalId = setInterval(function () {
    updateTimers();
  }, 1000);

  function updateTimers() {
    $.get("/timer/value", function (data) {
      var timeLeft = parseInt(data);
      var timePlayed = 3600 - timeLeft;
      var formattedTimeLeft = formatTime(timeLeft);
      var formattedTimePlayed = formatTime(timePlayed);
      $("#time-left").text(formattedTimeLeft);
      $("#time-played").text(formattedTimePlayed);
    });
  }

  function formatTime(seconds) {
    var minutes = Math.floor(seconds / 60);
    var remainingSeconds = seconds % 60;
    return (
      minutes +
      ":" +
      (remainingSeconds < 10 ? "0" : "") +
      remainingSeconds.toFixed(0)
    );
  }

  function updateSpeedDisplay() {
    var formattedSpeed = speed.toFixed(1);
    $("#speed-display").text("Timer Speed: " + formattedSpeed + "x");
  }

  function getTimerSpeed() {
    $.get("/timer/get-speed", function (data) {
      speed = parseFloat(data);
      updateSpeedDisplay();
    });
  }

  $("#start-game-button").click(function () {
    $.post("/timer/start", function (data) {
      console.log(data);
    }).done(function () {});
    intervalId = setInterval(function () {
      updateTimers();
    }, 1000);
    $("#continue-button").hide();
    $("#pause-button").show();
  });

  $("#end-game-button").click(function () {
    clearInterval(intervalId);
    updateTimers();
    $.post("/timer/stop", function (data) {
      console.log(data);
    });

    $.post("/reset_task_statuses", function (data) {
      console.log(data);
      fetchTasks(); // Refresh the list after resetting statuses
    });
    $.post("/reset_puzzles", function (data) {
      console.log(data);
      fetchTasks(); // Refresh the list after resetting statuses
    });
  });
  $("#snooze-game-button").click(function () {
    $.post("/snooze_game", function (data) {
      console.log(data);
    });
    // Display snoozed status in the nav
    $("#nav-snooze-status").text("Room Snoozed");
    // Show the "Wake" button
    $("#wake-button").show();
    $(".important-controls").hide();
  });
  $("#speed-up-button").click(function () {
    $.post("/timer/speed", { change: 0.1 }, function (data) {
      speed += 0.1;
      console.log(data);
      updateSpeedDisplay();
    });
  });

  $("#slow-down-button").click(function () {
    $.post("/timer/speed", { change: -0.1 }, function (data) {
      speed -= 0.1;
      console.log(data);
      updateSpeedDisplay();
    });
  });

  $("#reset-button").click(function () {
    $.post("/timer/reset-speed", function (data) {
      console.log(data);
      speed = 1;
      updateSpeedDisplay();
    });
  });
  function updateButtonState(pauseState) {
    if (pauseState) {
      $("#pause-button").hide();
      $("#continue-button").show();
    } else {
      $("#pause-button").show();
      $("#continue-button").hide();
    }
  }
  function getButtonState() {
    $.get("/timer/pause-state", function (data) {
      var pauseState = !data;
      updateButtonState(pauseState);
      console.log(data);
    });
  }

  $("#pause-button").click(function () {
    $.post("/timer/pause", function (data) {
      console.log(data);
      if (data === "Timer paused") {
        $("#pause-button").hide();
        $("#continue-button").show();
      }
    });
  });

  $("#continue-button").click(function () {
    $.post("/timer/continue", function (data) {
      console.log(data);
      if (data === "Timer continued") {
        $("#continue-button").hide();
        $("#pause-button").show();
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

$(document).ready(function () {
  // Check the snooze status from the JSON file
  $.get("/get_snooze_status", function (data) {
    if (data.snoozed) {
      // Display snoozed status in the nav
      $("#nav-snooze-status").text("Room Snoozed");
      // Show the "Wake" button
      $("#wake-button").show();
      $(".important-controls").hide();
    }
  });

  // Handle the "Wake" button click
  $("#wake-button").click(function () {
    // Send a request to reset snooze status to false
    $.post("/wake_room", function (data) {
      console.log(data);
      // Hide the "Wake" button
      $("#wake-button").hide();
      $(".important-controls").show();
      // Update the snooze status in the navigation
      $("#nav-snooze-status").hide();
    });
  });
});

function openMediaControlPage() {
  window.open("/media_control", "_blank", "height=400,width=400");
}
$(document).ready(function () {
  $("#resume-music-button").click(function () {
    $.ajax({
      type: "POST",
      url: "/resume_music",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
});

$(document).ready(function () {
  $("#stop-music-button").click(function () {
    $.ajax({
      type: "POST",
      url: "/stop_music",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
  $("#reboot-pi-mag").click(function () {
    $.ajax({
      type: "POST",
      url: "/reboot-maglock-pi",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
  $("#reboot-pi-music").click(function () {
    $.ajax({
      type: "POST",
      url: "/reboot-music-pi",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
  $("#backup-top-pi").click(function () {
    $.ajax({
      type: "POST",
      url: "/backup-top-pi",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
  $("#backup-middle-pi").click(function () {
    $.ajax({
      type: "POST",
      url: "/backup-middle-pi",
      success: function (response) {
        console.log(response);
      },
      error: function (error) {
        console.log(error);
      },
    });
  });
});

function updateState() {
  $.ajax({
    url: "/get_state", // Endpoint in your app.py to fetch the state
    type: "GET",
    success: function (response) {
      var state = response.state;
      $("#current-state").text("Walkman: " + state);
    },
    error: function () {
      $("#current-state").text("Walkman: unknown");
    },
  });
}
// Update the state every 5 seconds (5000 milliseconds)
setInterval(updateState, 5000);

$(document).ready(function () {
  function updateStatusDisplay() {
    $.get("/get_file_status", function (data) {
      $("#status-display").empty();

      const playingSongs = data.filter((entry) => entry.status === "playing");
      const pausedSongs = data.filter((entry) => entry.status === "paused");

      if (playingSongs.length > 0) {
        $("#music-list").empty();

        playingSongs.forEach((entry) => {
          const { filename, soundcard_channel } = entry;
          $("#status-display").append(`<div>${filename} is playing!</div>`);
          $("#music-list").append(`
                        <li>
                            ${filename}
                            <button class="button-style pause-button" data-file="${filename}" data-channel="${soundcard_channel}">Pause</button>
                        </li>
                    `);
        });
      } else {
        $("#music-list").empty(); // Clear the list if there are no songs playing
      }

      if (pausedSongs.length > 0) {
        $("#status-display").append("<div>Paused songs:</div>");
        pausedSongs.forEach((entry) => {
          const { filename, soundcard_channel } = entry;
          $("#status-display").append(`<div>${filename} is paused!</div>`);
          $("#music-list").append(`
                        <li>
                            ${filename}
                            <button class="button-style resume-button" data-file="${filename}" data-channel="${soundcard_channel}">Resume</button>
                        </li>
                    `);
        });
      }
    });
  }

  // Handle pause button click
  $(document).on("click", ".pause-button", function () {
    const selectedFile = $(this).data("file");
    const selectedChannel = $(this).data("channel");
    $.ajax({
      type: "POST",
      url: "/pause_music",
      data: { file: selectedFile, channel: selectedChannel },
      success: function (response) {
        console.log(response);
        updateStatusDisplay(); // Update the status display after pausing the song
      },
      error: function (error) {
        console.log(error);
      },
    });
  });

  // Handle resume button click
  $(document).on("click", ".resume-button", function () {
    const selectedFile = $(this).data("file");
    const selectedChannel = $(this).data("channel");
    $.ajax({
      type: "POST",
      url: "/resume_music",
      data: { file: selectedFile, channel: selectedChannel },
      success: function (response) {
        console.log(response);
        updateStatusDisplay(); // Update the status display after resuming the song
      },
      error: function (error) {
        console.log(error);
      },
    });
  });

  // Call the function initially and update the status display every 5 seconds
  updateStatusDisplay();
  setInterval(updateStatusDisplay, 5000);
});
function updatePiStatus() {
  $.ajax({
    url: "/get-pi-status",
    method: "GET",
    success: function (data) {
      // Update the table with the latest status data
      $("#status-table").html(data);
    },
    complete: function () {
      // Schedule the next update after 5 seconds
      setTimeout(updatePiStatus, 5000);
    },
  });
}
// Start updating status on page load
$(document).ready(function () {
  updatePiStatus();
});

async function fetchTasks() {
  console.log("Fetching tasks...");
  try {
    const response = await fetch("/get_task_status"); // Corrected route
    const tasks = await response.json();
    console.log("Fetched tasks:", tasks);

    const taskList = document.getElementById("task-list");
    taskList.innerHTML = ""; // Clear existing list

    tasks.forEach((task) => {
      // const taskListHidden = document.querySelector(".tasks-hidden");
      const taskTitle = document.querySelector(".task-title");
      const taskDescription = document.querySelector(".task-description");
      const currentState = document.querySelector(".current-state strong");
      const li = document.createElement("li");
      li.classList.add("task-list-item");
      li.textContent = `${task.task} - ${task.state}`;
      taskTitle.textContent = `${task.task}`;
      taskDescription.textContent = `${task.description}`;

      // Set the id attribute of the li element to the task name
      li.id = task.task;
      li.name = task.task;

      if (task.state !== "solved") {
        const buttonContainer = document.querySelector(".button-container");
        const button = document.createElement("button");
        buttonContainer.appendChild(button);
        button.textContent = "Mark as Solved";
        button.className = "button-style solved";
        button.addEventListener("click", () => markAsSolved(task.task));
        li.appendChild(button);
      }
      if (task.state == "solved") {
        const buttonContainer = document.querySelector(".button-container");
        const button = document.createElement("button");
        buttonContainer.appendChild(button);
        button.textContent = "Mark as Pending";
        button.className = "button-style pending";
        button.addEventListener("click", () => markAsPending(task.task));
        li.appendChild(button);
      }

      taskList.appendChild(li);
    });
  } catch (error) {
    console.error("Error fetching tasks:", error);
  }
}
const interval = setInterval(fetchTasks, 1500);
async function markAsSolved(taskName) {
  console.log(`Marking ${taskName} as solved...`);
  try {
    const response = await fetch(`/solve_task/${taskName}`, {
      method: "POST",
    });

    const data = await response.json();
    console.log(data.message);

    fetchTasks(); // Refresh the list
  } catch (error) {
    console.error("Error marking as solved:", error);
  }
}

async function markAsPending(taskName) {
  console.log(`Marking ${taskName} as solved...`);
  try {
    const response = await fetch(`/pend_task/${taskName}`, {
      method: "POST",
    });

    const data = await response.json();
    console.log(data.message);

    fetchTasks(); // Refresh the list
  } catch (error) {
    console.error("Error marking as solved:", error);
  }
}

fetchTasks();

document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("add-task-button")
    .addEventListener("click", function () {
      document.getElementById("task-modal").style.display = "block";
    });

  document.querySelector(".close-task").addEventListener("click", function () {
    console.log("Close button clicked");
    document.getElementById("task-modal").style.display = "none";
  });

  document
    .getElementById("save-task-button")
    .addEventListener("click", function () {
      const taskName = document.getElementById("task-name").value;
      const taskDescription = document.getElementById("task-description").value;

      if (taskName && taskDescription) {
        // Send a POST request to your Flask route to add a new task
        // Adjust the route and data as needed
        fetch("/add_task", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            task: taskName,
            description: taskDescription,
            state: "pending",
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            console.log(data.message);
            fetchTasks(); // Refresh the list
          })
          .catch((error) => console.error("Error adding task:", error));
      }

      document.getElementById("task-modal").style.display = "none";
    });
  document
    .getElementById("remove-task-button")
    .addEventListener("click", function () {
      populateTaskRemovalList(); // Populate the list of tasks
      document.getElementById("remove-modal").style.display = "block";
    });

  document
    .querySelector(".close-remove")
    .addEventListener("click", function () {
      document.getElementById("remove-modal").style.display = "none";
    });
  async function removeTask(taskName) {
    console.log(`Removing ${taskName}...`);
    try {
      const response = await fetch("/remove_task", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ task: taskName }),
      });

      const data = await response.json();
      console.log(data.message);
      fetchTasks(); // Refresh the list
    } catch (error) {
      console.error("Error removing task:", error);
    }
  }

  document
    .getElementById("confirm-remove-button")
    .addEventListener("click", function () {
      const selectedTask = document.querySelector(
        'input[name="task"]:checked'
      ).value;
      if (selectedTask) {
        const confirmRemove = confirm(
          `Are you sure you want to remove the task "${selectedTask}"?`
        );
        if (confirmRemove) {
          removeTask(selectedTask);
          document.getElementById("remove-modal").style.display = "none";
        }
      }
    });

  async function populateTaskRemovalList() {
    try {
      const response = await fetch("/get_task_status");
      const tasks = await response.json();

      const taskRemovalList = document.getElementById("task-removal-list");
      taskRemovalList.innerHTML = "";

      tasks.forEach((task) => {
        const li = document.createElement("li");
        const radio = document.createElement("input");
        radio.type = "radio";
        radio.name = "task";
        radio.value = task.task;
        li.textContent = `${task.task} - ${task.state}`;
        li.prepend(radio);
        taskRemovalList.appendChild(li);
      });
    } catch (error) {
      console.error("Error fetching tasks for removal:", error);
    }
  }
  const editButton = document.getElementById("edit-task-button");
  const editModal = document.getElementById("edit-modal");
  const taskEditList = document.getElementById("task-edit-list");
  const editTaskModal = document.getElementById("edit-task-modal");
  const editTaskNameInput = document.getElementById("edit-task-name");
  const editTaskDescriptionInput = document.getElementById(
    "edit-task-description"
  );
  const saveEditTaskButton = document.getElementById("save-edit-task-button");
  let previousSaveEditTaskListener;
  // Event listener for opening the edit modal
  editButton.addEventListener("click", function () {
    // Fetch the list of tasks from the server
    fetch("/get_tasks")
      .then((response) => response.json())
      .then((tasks) => {
        // Clear the previous task list
        taskEditList.innerHTML = "";

        // Populate the modal with tasks
        tasks.forEach((task) => {
          const li = document.createElement("li");
          const editTaskButton = document.createElement("button");
          editTaskButton.textContent = task.task;
          editTaskButton.classList.add("button-style");
          editTaskButton.addEventListener("click", function () {
            // Open the edit task modal and populate with current task info
            editTaskNameInput.value = task.task;
            editTaskDescriptionInput.value = task.description;
            editTaskModal.style.display = "block";
            // Save the current task being edited
            const currentTask = task;

            // Remove any previous event listeners
            if (previousSaveEditTaskListener) {
              saveEditTaskButton.removeEventListener(
                "click",
                previousSaveEditTaskListener
              );
            }

            // Add a new event listener for the save button
            previousSaveEditTaskListener = function () {
              // Get the edited task information
              const editedTaskName = editTaskNameInput.value;
              const editedTaskDescription = editTaskDescriptionInput.value;

              // Send the edited information to the server
              fetch("/edit_task", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  task: currentTask.task,
                  editedTaskName: editedTaskName,
                  editedTaskDescription: editedTaskDescription,
                }),
              })
                .then((response) => response.json())
                .then((data) => {
                  console.log(data.message);
                  // Close the edit task modal
                  editTaskModal.style.display = "none";
                  // Fetch tasks again to refresh the list
                  fetchTasks();
                })
                .catch((error) => {
                  console.error("Error editing task:", error);
                });
            };

            saveEditTaskButton.addEventListener(
              "click",
              previousSaveEditTaskListener
            );
          });
          li.appendChild(editTaskButton);
          taskEditList.appendChild(li);
        });

        // Show the edit modal
        editModal.style.display = "block";
      })
      .catch((error) => {
        console.error("Error fetching tasks:", error);
      });
    document
      .querySelector(".close-edit")
      .addEventListener("click", function () {
        document.getElementById("edit-modal").style.display = "none";
      });
    document
      .querySelector(".close-edit-task")
      .addEventListener("click", function () {
        document.getElementById("edit-task-modal").style.display = "none";
      });
  });
});
