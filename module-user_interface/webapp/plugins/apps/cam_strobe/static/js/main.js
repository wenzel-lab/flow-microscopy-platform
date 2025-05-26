
document.addEventListener('DOMContentLoaded', listImages);

function updateCamera() {
    var selectedCamera = document.getElementById('camera-select').value;
    fetch(cameraTypeUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ camera_name: selectedCamera })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateCameraConfig(selectedCamera);
                console.log('Camera set successfully');
            } else {
                console.error('Failed to set camera');
            }
        })
        .catch(error => console.error('Error setting camera:', error));
}

function updateCameraConfig(selectedCamera) {
    console.log('Selected Camera:', selectedCamera);
    fetch(cameraConfigUrl)
        .then(response => response.json())
        .then(data => {
            console.log('Camera Configurations:', data);
            const configForm = document.getElementById('camera-config-form');
            configForm.innerHTML = '';
            data.forEach(config => {
                const type_ = config.type;
                const unit = config.unit;
                const displayName = config.display_name;
                const name = config.name;
                const accessMode = config.access_mode;
                const writeEnabled = accessMode[1];
                const readEnabled = accessMode[0];
                if (type_ === "IntFeature" || type_ === "int") {
                    const valueRange = config.range;
                    const input = document.createElement('input');
                    const label = document.createElement('label');
                    label.for = displayName;
                    label.textContent = displayName + ' (' + unit + ')';
                    configForm.appendChild(label);
                    input.type = 'number';
                    input.name = name;
                    input.id = displayName;
                    input.className = 'form-control';
                    input.placeholder = displayName;
                    input.value = config.value;
                    // input.min = valueRange[0];
                    // input.max = valueRange[1];
                    if (writeEnabled) {
                        input.disabled = false;
                    }
                    else {
                        input.disabled = true;
                    }
                    configForm.appendChild(input);

                }

            });
            configForm.innerHTML += '<button type="button" class="btn btn-primary mt-3" onclick="setCameraConfig()">Update</button>';

        })
        .catch(error => console.error('Error fetching camera configurations:', error));
}

function setCameraConfig() {
    const configForm = document.getElementById('camera-config-form');
    const formData = new FormData(configForm);
    const configData = {};
    formData.forEach((value, key) => {
        configData[key] = value;
    });
    console
    fetch(cameraConfigUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Camera configuration set successfully');
            }
            else {
                console.error('Failed to set camera configuration');
            }
        }
        )
        .catch(error => console.error('Error setting camera configuration:', error));
}

// document.getElementById('play-button').addEventListener('click', function() {
//     document.getElementById('camera-frame').src = "{{ url_for('cam_strobe.get_frame') }}";
// });

// document.getElementById('stop-button').addEventListener('click', function() {
//     document.getElementById('camera-frame').src = '';
// });

function playCameraFrame() {
    console.log('Playing camera frame');
    const cameraFrame = document.getElementById('camera-frame');
    cameraFrame.src = framesUrl;
    cameraFrame.onload = function () {
        axios.get("/api/pi_camera_32/get-current-resolution")
            .then(response => {
                const frameWidth = response.data.width;
                const frameHeight = response.data.height;
                const cameraContainer = document.getElementById('camera-container');
                cameraContainer.style.width = frameWidth + 'px';
                cameraContainer.style.height = frameHeight + 'px';
                console.log('Frame dimensions:', frameWidth, frameHeight);
            }
            )
            .catch(error => console.error('Error getting camera resolution:', error));

        // const frameWidth = 480
        // const frameHeight = 480
        // const cameraContainer = document.getElementById('camera-container');
        // cameraContainer.style.width = frameWidth + 'px';
        // cameraContainer.style.height = frameHeight + 'px';
        // console.log('Frame dimensions:', frameWidth, frameHeight);
    };
}

function stopCameraFrame() {
    document.getElementById('camera-frame').src = '';
}

function capture() {
    fetch(makeCaptureUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            console.log('Capture response:', data);
            if (data.status === 'success') {
                const newName = prompt('Enter a new name for the captured image:');
                if (newName) {
                    fetch(captureRenameUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ old_name: data.frame_name, new_name: newName })
                    })
                        .then(renameResponse => renameResponse.json())
                        .then(renameData => {
                            console.log('Rename response:', renameData);
                            if (renameData.status === 'success') {
                                alert('Image renamed successfully!');
                            } else {
                                alert('Failed to rename image.');
                            }
                        })
                        .catch(error => console.error('Error renaming image:', error));
                }
                listImages();
            }
        })
        .catch(error => console.error('Error capturing image:', error));
};

const itemsPerPage = 10;
function fetchCaptures(page) {
    fetch(`${listCapturesUrl}?page=${page}&per_page=${itemsPerPage}`)
        .then(response => response.json())
        .then(data => {
            const captureList = document.getElementById('capture-list');
            captureList.innerHTML = '';
            const table = document.createElement('table');
            table.className = 'table table-striped';
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Date</th>
                    <th scope="col">View</th>
                </tr>
            `;
            table.appendChild(thead);
            const tbody = document.createElement('tbody');
            data.forEach(capture => {
                const captureName = capture[0];
                const captureDate = capture[1];
                const row = document.createElement('tr');
                const nameCell = document.createElement('td');
                nameCell.textContent = captureName;
                const dateCell = document.createElement('td');
                dateCell.textContent = captureDate;
                const actionCell = document.createElement('td');
                const captureUrl = getCaptureBaseUrl + "/" + captureName;
                actionCell.innerHTML = `<a href="${captureUrl}" target="_blank"><i class='bi bi-image'></i></a>`;
                row.appendChild(nameCell);
                row.appendChild(dateCell);
                row.appendChild(actionCell);
                tbody.appendChild(row);
            });
            table.appendChild(tbody);
            captureList.appendChild(table);
            currentPage = page;
        })
        .catch(error => console.error('Error fetching captures:', error));
}

let currentPage = 1;
function listImages() {
    document.getElementById('prev-page').addEventListener('click', function (event) {
        event.preventDefault();
        if (currentPage > 1) {
            fetchCaptures(currentPage - 1);
        }
    });

    document.getElementById('next-page').addEventListener('click', function (event) {
        event.preventDefault();
        fetchCaptures(currentPage + 1);
    });

    fetchCaptures(currentPage);
};

function strobe_period() {
    var period = document.getElementById('input_strobe_period_us').value;
    fetch(strobePeriodUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ strobe_period_us: period })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Strobe period set successfully');
            } else {
                console.error('Failed to set strobe period');
            }
        })
        .catch(error => console.error('Error setting strobe period:', error));
}

function strobe_enable(enabled) {
    fetch(setStrobeEnableUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ strobe_enable: enabled })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Strobe enabled successfully');
            } else {
                console.error('Failed to enable strobe');
            }
        })
        .catch(error => console.error('Error enabling strobe:', error));
}