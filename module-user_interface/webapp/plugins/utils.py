import json


CONFIG_FILE = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"plugins": {"devices": {}, "apps": {}}}


def save_config(config):
    config_data = load_config()
    config_data.update(config)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)


def web_frame_generator(camera, config: dict):
    for frame in camera.generate_frames(config):
        yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame.tobytes() + b"\r\n"