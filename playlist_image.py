from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

def create_image(colors, playlist_name):
    # add '#' to each color
    new_colors = []
    for color in colors:
        if color[0] != "#":
            new_colors.append("#" + color)

    def create_gradient(width, height, colors):
        gradient = Image.new('RGB', (width, height), color=0)
        draw = ImageDraw.Draw(gradient)

        # Create linear gradient
        for i, color in enumerate(colors):
            start = (0, height * i // len(colors))
            end = (width, height * (i + 1) // len(colors))
            draw.rectangle([start, end], fill=color)

        return gradient

    def add_text(image, text, font_size, font_color, position):
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("SuezOne-Regular.ttf", font_size)
        draw.text(position, text, fill=font_color, font=font)

    def apply_blur(image, radius=5):
        return image.filter(ImageFilter.GaussianBlur(radius))

    width = 512
    height = 512
    gradient = create_gradient(width, height, new_colors)
    gradient = apply_blur(gradient)

    image = Image.new('RGB', (width, height))
    image.paste(gradient)

    font_size = 30
    font_color = (255, 255, 255)
    position = (width // 2 - font_size * len(playlist_name) // 4, height // 2 - font_size // 2)
    add_text(image, playlist_name, font_size, font_color, position)

    image.save('playlist.jpg')