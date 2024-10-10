# goTerrainThumbnailGenerator
Python code to update a GPKG file with icons of the photos where present

You will need to install Python on your machine to run this, and preferably update the windows path to point at Python as that will then enable you to double click this bit of code in explorer.

Code will loop through all records in the selected GKPG file and if there is a BLOB in photo1 field, crop it square and replace the existing generic iconData blob field.

Converted GKPG file can then be dropped onto QGIS which will then show square thumbnails.
