import os
import sys
from PIL import Image
import pyocr

class ImageData:
    tesseract_path = 'C:\Program Files\Tesseract-OCR'
    if tesseract_path not in os.environ['PATH'].split(os.pathsep):
        os.environ['PATH'] += os.pathsep + tesseract_path

    def image_to_text(self, image, language):
        tools = pyocr.get_available_tools()
        if len(tools) == 0:
            print('OCRエンジンが指定されていません')
            sys.exit(1)
        else:
            tool = tools[0]

        img = Image.open(image)
        img = img.convert('RGB')

        builder = pyocr.builders.TextBuilder(tesseract_layout = 6)
        result = tool.image_to_string(img, lang=language, builder = builder)
        return result