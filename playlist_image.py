import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_image(colors, playlist_name):
    # add '#' to each color
    new_colors = []
    for color in colors:
        if color[0] != "#":
            new_colors.append("#" + color)
        else:
            new_colors.append(color)

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def generate_mesh_gradient(width, height, color1, color2, color3):
        img = Image.new('RGB', (width, height))

        # Convert hex colors to RGB
        color1_rgb = hex_to_rgb(color1)
        color2_rgb = hex_to_rgb(color2)
        color3_rgb = hex_to_rgb(color3)

        # Create a gradient mesh
        for y in range(height):
            for x in range(width):
                # Calculate color interpolation
                ratio1 = x / (width - 1)
                ratio2 = y / (height - 1)
                r = int((1 - ratio1) * ((1 - ratio2) * color1_rgb[0] + ratio2 * color2_rgb[0]) + ratio1 * color3_rgb[0])
                g = int((1 - ratio1) * ((1 - ratio2) * color1_rgb[1] + ratio2 * color2_rgb[1]) + ratio1 * color3_rgb[1])
                b = int((1 - ratio1) * ((1 - ratio2) * color1_rgb[2] + ratio2 * color2_rgb[2]) + ratio1 * color3_rgb[2])
                img.putpixel((x, y), (r, g, b))

        return img

    def add_text(image, text, font_size, font_color, position):
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("SuezOne-Regular.ttf", font_size)
        draw.text(position, text, fill=font_color, font=font)

    def apply_blur(image, radius=5):
        return image.filter(ImageFilter.GaussianBlur(radius))

    width = 500
    height = 500
    gradient = generate_mesh_gradient(width, height, new_colors[0], new_colors[1], new_colors[2])
    gradient = apply_blur(gradient, 5)

    image = Image.new('RGB', (width, height))
    image.paste(gradient)

    font_size = 45
    font_color = (255, 255, 255)
    position = (width // 2 - font_size * len(playlist_name) // 4, height // 2 - font_size // 2)
    add_text(image, playlist_name, font_size, font_color, position)

    image.save('playlist.jpg')


def base64_image():
    with open("playlist.jpg", "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == "__main__":
    colors = ["#FDB813", "#00BFA5", "#EC4C47"]
    playlist_name = '"Summer Breeze"'
    create_image(colors, playlist_name)
    img = Image.open('playlist.jpg')
    img.show()