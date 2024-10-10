# This script will convert photo1 in the GoTerrain app' GPKG file into a cropped
# square icon. QGIS needs tweaking to use this instead of photo1 by 

import sqlite3
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as mb
from PIL import Image, ImageDraw
import io
import re


def add_corners(im, rad=50, bg=True, bgCol='white', bgPix=50):

    # Generate background
    bg_im = Image.new('RGB', tuple(x+(bgPix*2) for x in im.size), bgCol)
    ims = [im if not bg else im, bg_im]
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    for i in ims:
        alpha = Image.new('L', i.size, 'white')
        w, h = i.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        i.putalpha(alpha)
    bg_im.paste(im, (bgPix, bgPix), im)
    # Resize image as it does not nee to be big
    newsize = (100, 100)
    im = im.resize(newsize)
    return im if not bg else bg_im

def makeThumbnail(blob_data):
    img = Image.open(blob_data)
    width, height = img.size
    if width < height:
        box = (0,(height-width)/2, width, width+((height-width)/2))
        img2 = img.crop(box)
        img2 = add_corners(img2)
    elif width > height:
        box = ((width-height)/2,0, height+((width-height)/2),height)
        print ("box:", box)
        img2 = img.crop(box)
        img2 = add_corners(img2)
    else:
        #leave it unchanged
        img2 = img
        img2 = add_corners(img2)
        print("left unchanged")

    if img2.mode in ("RGBA", "P"):
        img2 = img2.convert("RGB")
    return img2

def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(title="Select a file")
    return file_path

def image_to_byte_array(image: Image) -> bytes:
    # BytesIO is a file-like buffer stored in memory
    imgByteArr = io.BytesIO()
    # image.save expects a file-like as a argument

    image.save(imgByteArr, format='JPEG')
    # Turn the BytesIO object back into a bytes object
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr


def update_blob(conn, record_id, blob_data):
    try:
        # Connect to the SQLite database  
        cursor = conn.cursor()
        # Find the waypoint table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name like '%waypoints';")
        # Update the BLOB data field in the record
        row = cursor.fetchone()
        print(row[0])
        sql_update_blob_query = """ UPDATE """ + row[0] + """
                                    SET iconData = ?
                                    WHERE id = ?"""

        cursor.execute(sql_update_blob_query, (blob_data, record_id))
        conn.commit()
        print(record_id, "icon updated successfully")

    except sqlite3.Error as error:
        print("Failed to update icon data", error)

def update_qgis_expression(conn):
    # Change the QGIS Expression to always use IconData as icon rather than photo1
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, styleqml FROM layer_styles;")
        row = cursor.fetchone()
        oldStr = "coalesce\(\&quot;photo1\&quot;,\&quot;iconData\&quot;\)"
        newStr = "&quot;iconData&quot;"
        newqml = re.sub(oldStr, newStr, row[1])
        sql_update_blob_query = """ UPDATE layer_styles
                                    SET styleqml = ?
                                    WHERE id = ?"""        
        cursor.execute(sql_update_blob_query, (newqml, row[0]))
        conn.commit()
        print("QGIS Expression updated")
    except sqlite3.Error as error:
        print("Failed to update QGIS Expression:", error)

while True:
    file_path = select_file()
    print (file_path)


    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        # Find the waypoint table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name like '%waypoints';")
        # Update the BLOB data field in the record
        row = cursor.fetchone()
        cursor.execute("SELECT id, name, photo1 FROM " + row[0] + ";")
        rows = cursor.fetchall()

        # Loop through each record and convert to a square thumbnail and replace the default icon
        for row in rows:
            print(row[0], row[1])
            if row[2] != None:
                update_blob(conn, row[0], image_to_byte_array(makeThumbnail(io.BytesIO(row[2]))))
                
        #edit the qgis expression so it uses the new thumbnails
        update_qgis_expression(conn)
        
    except sqlite3.Error as error:
        print("Failed doh!:", error)

    finally:
        if conn:
            conn.close()

    res=mb.askquestion('GKPG Update', 'Do another file?')
    if res == 'no' :
        break




    

