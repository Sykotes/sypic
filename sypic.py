import os
import sys
from typing import Any

import glfw
import glm
import moderngl
import numpy as np
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
Image.MAX_IMAGE_PIXELS = 250_000_000

class Keys:
    def __init__(self) -> None:
        self.keys_down = set()
        self.just_pressed = set()
        self.last_keys_down = set()

    def key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:
            self.keys_down.add(key)
        elif action == glfw.RELEASE:
            self.keys_down.discard(key)


class Sypic:
    def __init__(self) -> None:
        self.files: list[str] = (
            self.get_image_file_paths()
        )  # full paths to all image files
        if not self.files:
            print("No images at provided path")
            sys.exit()

        self.file_index = 0
        self.file_max = len(self.files)

        self.window = self.setup_window()

        glfw.make_context_current(self.window)
        self.ctx = moderngl.create_context()

        self.keys = Keys()
        glfw.set_key_callback(self.window, self.keys.key_callback)

        def framebuffer_size_callback(_, width, height):
            self.ctx.viewport = (0, 0, width, height)

        glfw.set_framebuffer_size_callback(self.window, framebuffer_size_callback)

        width, height = glfw.get_framebuffer_size(self.window)
        self.ctx.viewport = (0, 0, width, height)

        vertices = np.array(
            # fmt: off
            [
                -1.0, -1.0, 0.0, 1.0,
                1.0, -1.0, 1.0, 1.0,
                -1.0, 1.0, 0.0, 0.0,
                1.0, 1.0, 1.0, 0.0,
            ],
            # fmt: on
            dtype="f4",
        )
        vbo = self.ctx.buffer(vertices)

        vert_shader_path = os.path.join(SCRIPT_DIR, "shader.vert")
        frag_shader_path = os.path.join(SCRIPT_DIR, "shader.frag")

        with open(vert_shader_path, "r", encoding="UTF-8") as f:
            vertex_shader = f.read()
        with open(frag_shader_path, "r", encoding="UTF-8") as f:
            fragment_shader = f.read()

        self.program = self.ctx.program(
            vertex_shader=vertex_shader, fragment_shader=fragment_shader
        )

        self.vao = self.ctx.simple_vertex_array(
            self.program,
            vbo,
            "in_vert",
            "in_uv",
        )

        try:
            self.image = Image.open(self.files[0]).convert("RGB")
        except FileNotFoundError:
            print("ERROR: File not found")
            glfw.terminate()
            sys.exit()

        self.tex = self.ctx.texture(self.image.size, 3, self.image.tobytes())
        self.tex.build_mipmaps()
        self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex.use()

    def get_image_file_paths(self) -> list[str]:
        path_arg = sys.argv[1]
        files = []
        if os.path.isfile(path_arg):
            new_path = os.path.abspath(path_arg)
            files.append(new_path)
        elif os.path.isdir(path_arg):
            for f in os.listdir(path_arg):
                if os.path.isfile(os.path.join(path_arg, f)):
                    new_path = os.path.abspath(os.path.join(path_arg, f))
                    files.append(new_path)
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        image_files = [f for f in files if f.lower().endswith(tuple(image_extensions))]

        return image_files

    def setup_window(self) -> Any:
        if not glfw.init():
            raise Exception("GLFW init failed")

        window = glfw.create_window(800, 600, "sypic", None, None)
        if not window:
            glfw.terminate()
            raise Exception("GLFW window creation failed")

        return window

    def change_image(self, back=False) -> None:
        if back == True:
            self.file_index = (self.file_index - 1) % self.file_max
        else:
            self.file_index = (self.file_index + 1) % self.file_max
        new_image = Image.open(self.files[self.file_index]).convert("RGB")

        self.tex.release()
        self.tex = self.ctx.texture(new_image.size, 3, new_image.tobytes())
        self.tex.build_mipmaps()
        self.tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.tex.use()

        self.image.close()
        self.image = new_image

    def handle_events(self) -> None:
        glfw.poll_events()
        self.keys.just_pressed = self.keys.keys_down - self.keys.last_keys_down

        if glfw.KEY_J in self.keys.just_pressed or glfw.KEY_L in self.keys.just_pressed:
            self.change_image()

        if glfw.KEY_K in self.keys.just_pressed or glfw.KEY_H in self.keys.just_pressed:
            self.change_image(back=True)

    def run(self) -> None:
        while not glfw.window_should_close(self.window):
            self.handle_events()

            w_size = glfw.get_window_size(self.window)
            if self.program.get("in_w_ratio", False) != False:
                self.program["in_w_ratio"] = glm.vec2(w_size)

            if self.program.get("in_i_ratio", False) != False:
                self.program["in_i_ratio"] = glm.vec2(self.image.size)

            self.ctx.clear(0.3, 0.3, 0.3, 1.0)
            self.vao.render(moderngl.TRIANGLE_STRIP)

            glfw.swap_buffers(self.window)
            self.keys.last_keys_down = set(self.keys.keys_down)

        glfw.terminate()


def print_help() -> None:
    print("Usage: sypic <directory or file>")
    print("Options:")
    print("  -h       Display this information.")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print_help()

    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print_help()

    if len(sys.argv) > 2:
        print("Only provide one path")
        print("Use -h to show help")

    sypic = Sypic()
    sypic.run()


if __name__ == "__main__":
    main()
