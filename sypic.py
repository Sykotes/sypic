import argparse
import math
import os
import re
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
    def __init__(self, path_arg: str) -> None:
        self.filter_nearest = False
        self.clear_color = (0.3, 0.3, 0.3, 1.0)
        self.preload_enabled: bool = True

        self.files: list[str] = self.get_image_file_paths(
            path_arg
        )  # full paths to all image files
        if not self.files:
            print("No images at provided path")
            sys.exit()
        self.file_index = 0
        self.file_max = len(self.files)

        self.window = self.setup_window()

        glfw.make_context_current(self.window)
        self.ctx = moderngl.create_context()
        self.ctx.gc_mode = "auto"
        self.ctx.enable(moderngl.BLEND)

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

        self.image_sizes: list[tuple[int, int]] = [(0, 0)] * self.file_max
        self.loaded_textures: list = [None] * self.file_max
        self.max_load: int = 1
        if self.preload_enabled:
            self.max_load: int = 2
        self.should_unload: bool = False
        self.should_preload: bool = False

    def get_image_file_paths(self, path_arg: str) -> list[str]:
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
        old_index = self.file_index
        if back == True:
            self.file_index = (self.file_index - 1) % self.file_max
        else:
            self.file_index = (self.file_index + 1) % self.file_max

        if self.loaded_textures[self.file_index] == None:
            image = Image.open(self.files[self.file_index]).convert("RGBA")
            self.image_sizes[self.file_index] = image.size
            self.loaded_textures[self.file_index] = self.ctx.texture(
                self.image_sizes[self.file_index], 4, image.tobytes()
            )
            self.loaded_textures[self.file_index].build_mipmaps()
            if self.filter_nearest == True:
                self.loaded_textures[self.file_index].filter = (
                    moderngl.NEAREST,
                    moderngl.NEAREST,
                )
            else:
                self.loaded_textures[self.file_index].filter = (
                    moderngl.LINEAR_MIPMAP_LINEAR,
                    moderngl.LINEAR,
                )

        self.loaded_textures[self.file_index].use()
        if self.max_load <= 1:
            self.loaded_textures[old_index].release()
            self.loaded_textures[old_index] = None

    def handle_events(self) -> None:
        glfw.poll_events()
        self.keys.just_pressed = self.keys.keys_down - self.keys.last_keys_down

        if glfw.KEY_J in self.keys.just_pressed or glfw.KEY_L in self.keys.just_pressed:
            self.change_image()

        if glfw.KEY_K in self.keys.just_pressed or glfw.KEY_H in self.keys.just_pressed:
            self.change_image(back=True)

    def run(self) -> None:
        try:
            image = Image.open(self.files[0]).convert("RGBA")
        except FileNotFoundError:
            print("ERROR: File not found")
            glfw.terminate()
            sys.exit()

        self.image_sizes[self.file_index] = image.size
        self.loaded_textures[self.file_index] = self.ctx.texture(
            self.image_sizes[self.file_index], 4, image.tobytes()
        )
        image.close()
        self.loaded_textures[self.file_index].build_mipmaps()
        if self.filter_nearest == True:
            self.loaded_textures[self.file_index].filter = (
                moderngl.NEAREST,
                moderngl.NEAREST,
            )
        else:
            self.loaded_textures[self.file_index].filter = (
                moderngl.LINEAR_MIPMAP_LINEAR,
                moderngl.LINEAR,
            )

        self.loaded_textures[self.file_index].use()

        while not glfw.window_should_close(self.window):
            if self.should_unload:
                allowed_loaded: list[int] = [self.file_index]
                for i in range(1, math.ceil(self.max_load / 2) + 1):
                    allowed_loaded.append((self.file_index + i) % self.file_max)
                    allowed_loaded.append((self.file_index - i) % self.file_max)

                for i in range(self.file_max):
                    if i in allowed_loaded:
                        continue

                    if self.loaded_textures[i]:
                        self.loaded_textures[i].release()
                        self.loaded_textures[i] = None

            if self.should_preload:
                next_file_index = (self.file_index + 1) % self.file_max

                if self.loaded_textures[next_file_index] == None:
                    image = Image.open(self.files[next_file_index]).convert("RGBA")
                    self.image_sizes[next_file_index] = image.size
                    self.loaded_textures[next_file_index] = self.ctx.texture(
                        self.image_sizes[next_file_index], 4, image.tobytes()
                    )
                    self.loaded_textures[next_file_index].build_mipmaps()
                    if self.filter_nearest == True:
                        self.loaded_textures[next_file_index].filter = (
                            moderngl.NEAREST,
                            moderngl.NEAREST,
                        )
                    else:
                        self.loaded_textures[next_file_index].filter = (
                            moderngl.LINEAR_MIPMAP_LINEAR,
                            moderngl.LINEAR,
                        )

                    image.close()

            self.handle_events()

            w_size = glfw.get_window_size(self.window)
            if self.program.get("in_w_ratio", False) != False:
                self.program["in_w_ratio"] = glm.vec2(w_size)

            if self.program.get("in_i_ratio", False) != False:
                self.program["in_i_ratio"] = glm.vec2(self.image_sizes[self.file_index])

            self.ctx.clear(*self.clear_color)
            self.vao.render(moderngl.TRIANGLE_STRIP)

            glfw.swap_buffers(self.window)
            self.keys.last_keys_down = set(self.keys.keys_down)

            if self.max_load > 1 and self.preload_enabled:
                self.should_preload = True

            if self.max_load > 1:
                self.should_unload = True

        # for texture in self.loaded_textures:
        # texture.release()

        glfw.terminate()


def valid_hex_color(value: str) -> str:
    if not re.match(r"^#?[0-9a-fA-F]{6}$", value):
        raise argparse.ArgumentTypeError(f"{value} is not a valid hex color code")
    return value if value.startswith("#") else f"#{value}"


def valid_sort_option(value: str) -> bool:
    raise argparse.ArgumentTypeError("sorting is not yet implemented")
    options = {
        "alpha",
        "dm",
        "dc",
    }

    if value not in options:
        raise argparse.ArgumentTypeError(f"{value} is not a valid sorting option")

    return True


def valid_max_load(value: str) -> int:
    try:
        max_load = int(value)
        if max_load < 1:
            raise argparse.ArgumentTypeError(
                f"{value} is not an integer greater than 0"
            )
    except:
        raise argparse.ArgumentTypeError(f"{value} is not an integer greater than 0")

    return max_load


def hex_to_rgb(hex_code: str) -> tuple[float, float, float]:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) != 6:
        raise ValueError("Hex code must be 6 characters long.")

    r = int(hex_code[0:2], 16) / 255.0
    g = int(hex_code[2:4], 16) / 255.0
    b = int(hex_code[4:6], 16) / 255.0

    return (r, g, b)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A minimal GPU rendered image viewer made with python"
    )
    parser.add_argument(
        "-bg",
        "--background",
        type=valid_hex_color,
        help="Background colour in hex, e.g. #ff00ff",
    )
    parser.add_argument(
        "-s",
        "--sort",
        type=valid_sort_option,
        help="[NOT IMPLEMENTED] Sort images by the chosen method. Default is alphabetical",
    )
    parser.add_argument(
        "-m",
        "--max-loaded-images",
        type=valid_max_load,
        help="A maximum amount of cached images (this can use a lot of VRAM/ RAM)",
    )
    parser.add_argument(
        "-n",
        "--filter-nearest",
        action="store_true",
        help="Use nearest texture filtering (good for pixel art)",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Reverse the sorting order",
    )
    parser.add_argument(
        "--disable-preload",
        action="store_true",
        help="Disable preloading the next image (saves VRAM/ RAM but is slower)",
    )
    parser.add_argument("path", help="Path to image file or directory with images")

    args = parser.parse_args()

    sypic = Sypic(args.path)

    if args.filter_nearest:
        sypic.filter_nearest = True

    if args.disable_preload:
        sypic.preload_enabled = False

    if args.background:
        sypic.clear_color = hex_to_rgb(args.background) + (1.0,)

    if args.max_loaded_images:
        sypic.max_load = args.max_loaded_images

    sypic.run()


if __name__ == "__main__":
    main()
