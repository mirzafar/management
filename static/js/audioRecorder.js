let mediaRecorder;
let audioChunks = [];

const startRecordingButton = $('#startRecording');
const stopRecordingButton = $('#stopRecording');
const clearRecordingButton = $('#clearRecording');
const successRecordingButton = $('#successRecording');
const audioPlayer = $('#audioPlayer')[0];

function clearRecorder() {
    audioChunks = [];
    audioPlayer.src = '';
    startRecordingButton.prop('disabled', false);
}

navigator.mediaDevices.getUserMedia({audio: true})
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, {type: 'audio/wav'});
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayer.src = audioUrl;
        };

        startRecordingButton.on('click', () => {
            mediaRecorder.start();
            startRecordingButton.prop('disabled', true);
            stopRecordingButton.prop('disabled', false);
        });

        stopRecordingButton.on('click', () => {
            mediaRecorder.stop();
            startRecordingButton.prop('disabled', false);
            stopRecordingButton.prop('disabled', true);
        });

        clearRecordingButton.on('click', () => {
            audioChunks = [];
            audioPlayer.src = '';
        });

        successRecordingButton.on('click', () => {
            if (audioChunks.length !== 0) {
                const audioBlob = new Blob(audioChunks, {type: 'audio/wav'});

                const formData = new FormData();
                formData.append('file', audioBlob, 'recorded_audio.wav');

                fetch('/upload/', {
                    method: 'POST',
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        let trigger_name = $('#audioInput').parents('.col-sm-9').data('name');
                        let input_name = $('#audioInput').closest('.col-sm-9').find('[name="' + trigger_name + '"]');
                        alertShow('success', 'Loaded');
                        input_name.val(String(data['file_name']));
                        clearRecorder();
                    })
                    .catch(error => {
                        console.log('Error sending audio to the server', error)
                        alertShow('error', 'Error sending audio to the server');
                    });
            }
        });
    })
    .catch(error => {
        console.error('Error accessing microphone:', error);
    });