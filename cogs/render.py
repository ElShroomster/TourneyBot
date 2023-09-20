import discord
from PIL.ImageFont import FreeTypeFont
from PIL import Image, ImageFont, ImageDraw
import io

FONT_REGULAR: FreeTypeFont = ImageFont.truetype(f'./data/BebasNeue-Regular.ttf', 37)

data = None
with open('./data/lb.png', 'rb') as f:
    data = f.read()

def leaderboard():

    def write_centered(box_x, box_y, width, height, text, debug=False):
        x1, y1, x2, y2 = draw.textbbox((0, 0), text, font=FONT_REGULAR)

        midx = box_x + (width/2)
        midy = box_y + (height/2) - 5

        text_width = x2 - x1
        text_height = y2 - y1

        x = midx - (text_width/2)
        y = midy - (text_height/2)

        if debug:
            draw.rectangle((box_x, box_y, box_x + width, box_y + height), fill="#ff0000", width=0)

        draw.text((x, y), text, font=FONT_REGULAR, fill="#000")


    image = Image.open(io.BytesIO(data))
    draw = ImageDraw.Draw(image)

    for i in range(0, 8):

        text = "ABCD" + str(i) * (i + 1)

        x = 162
        width = 385
        write_centered(x, 175 + i*52.25, width, 49, text, debug=False)

        x += width

        width = 110
        write_centered(x, 175 + i*52.25, width, 49, "123", debug=False)

        x += width

        write_centered(x, 175 + i*52.25, width, 49, "456", debug=False)

        x += width

        width = 100
        write_centered(x, 175 + i*52.25, width, 49, "789", debug=False)

        x += width

        write_centered(x, 175 + i*52.25, width, 49, "999", debug=False)

        x += width

        write_centered(x, 175 + i*52.25, 118, 49, "10111", debug=False)

    img_data = io.BytesIO()

    # image.save expects a file-like as a argument
    image.save(img_data, format=image.format)

    d = img_data.getvalue()

    img_data.close()

    return d