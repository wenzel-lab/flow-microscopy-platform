const socket = io('ws://127.0.0.1:5000/cam_strobe/heaters', {
    transports: ['websocket'],  // Force WebSocket transport
});

socket.on('connect', () => {
    console.log('Connected');
});

socket.on('data', (data) => {
    console.log('Namespace event received:', data);
    for 
});

socket.on('disconnect', () => {
    console.log('Disconnected');
});