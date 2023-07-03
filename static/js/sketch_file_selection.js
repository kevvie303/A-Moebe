$(document).ready(function() {
    $('.play-button').click(function() {
        var selectedFile = $(this).data('file');
        $.ajax({
            type: 'POST',
            url: '/play_music',
            data: {file: selectedFile},
            success: function(response) {
                console.log(response);
                window.close(); // Close the window after successful playback
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});