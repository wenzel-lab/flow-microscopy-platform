

# def web_frame_generator(camera, config: dict):
#     for frame in camera.generate_frames(config):
#         yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame.tobytes() + b"\r\n"