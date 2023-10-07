from PIL.ImageFont import FreeTypeFont
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands
import io
import random
import json

FONT_REGULAR: FreeTypeFont = ImageFont.truetype(f'./data/BebasNeue-Regular.ttf', 32)

FONT_SMALLER: FreeTypeFont = ImageFont.truetype(f'./data/BebasNeue-Regular.ttf', 28)

lbs = []
# Add sunset background
#with open('./data/lb.png', 'rb') as f:
    #lbs.append(f.read())

with open('./data/lb.png', 'rb') as f:
    lbs.append(f.read())

mapping = None
with open("./data/map.json", "r", encoding="utf-8") as f:
    f.seek(0)
    mapping = json.load(f)

async def leaderboard(ctx, scores, bracket, bot: commands.Bot):

    def write_centered(box_x, box_y, width, height, text, debug=False, font=FONT_REGULAR):
        x1, y1, x2, y2 = draw.textbbox((0, 0), text, font=FONT_REGULAR)

        midx = box_x + (width/2)
        midy = box_y + (height/2) - 5

        text_width = x2 - x1
        text_height = y2 - y1

        x = midx - (text_width/2)
        y = midy - (text_height/2)

        if debug:
            draw.rectangle((box_x, box_y, box_x + width, box_y + height), fill="#ff0000", width=0)

        if text_width > width:
            print('Text too big...')

        draw.text((x, y), text, font=font, fill="#000")
    
    image = Image.open(io.BytesIO(random.choice(lbs)))
    draw = ImageDraw.Draw(image)

    write_centered(110, 50, 480, 20, bracket, False)

    for i, entry in enumerate(scores):

        if i > 7:
            break

        ids = entry["members"]
        names = []

        for _id in ids:
            if _id in mapping:
                names.append(mapping[_id])

            else:
                try:
                    user = await ctx.guild.fetch_member(int(_id))
                    names.append(f'{user.display_name}')
                except:
                    user = await bot.fetch_user(int(_id))
                    names.append(f'{user.display_name}')

        text = " & ".join(names)

        x = 162
        width = 385
        write_centered(x, 175 + i*52.25, width, 49, text, debug=False)

        x += width

        width = 110
        write_centered(x, 175 + i*52.25, width, 49, str(entry["total"]), debug=False)

        x += width

        write_centered(x, 175 + i*52.25, width, 49, str(entry["finals"]), debug=False)

        x += width

        width = 100
        write_centered(x, 175 + i*52.25, width, 49, str(entry["bedBreaks"]), debug=False)

        x += width

        write_centered(x, 175 + i*52.25, width, 49, str(entry["survival"]), debug=False)

        x += width

        write_centered(x, 175 + i*52.25, 118, 49, str(entry["position"]), debug=False)

    img_data = io.BytesIO()

    # image.save expects a file-like as a argument
    image.save(img_data, format=image.format)

    d = img_data.getvalue()

    img_data.close()

    return d