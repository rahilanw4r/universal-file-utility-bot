import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.image_converter import convert_image, compress_to_target


class ImageConverterTests(unittest.TestCase):
    def test_png_conversion_preserves_transparency(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            target = Path(tmp) / "converted.png"
            image = Image.new("RGBA", (4, 4), (255, 0, 0, 0))
            image.putpixel((1, 1), (0, 255, 0, 255))
            image.save(source)
            convert_image(source, target, "png")
            with Image.open(target) as result:
                self.assertEqual(result.mode, "RGBA")
                self.assertEqual(result.getpixel((0, 0))[3], 0)
                self.assertEqual(result.getpixel((1, 1)), (0, 255, 0, 255))

    def test_webp_conversion_keeps_alpha(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "a.png", Path(tmp) / "b.webp"
            Image.new("RGBA", (8, 8), (10, 20, 30, 0)).save(source)
            convert_image(source, target, "webp")
            with Image.open(target) as result:
                self.assertEqual(result.mode, "RGBA")
                self.assertEqual(result.getpixel((0, 0))[3], 0)

    def test_jpeg_conversion_flattens_transparency(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "a.png", Path(tmp) / "b.jpg"
            Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(source)
            convert_image(source, target, "jpg")
            with Image.open(target) as result:
                self.assertEqual(result.mode, "RGB")
                self.assertEqual(result.getpixel((0, 0)), (255, 255, 255))

    def test_compression_respects_reasonable_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "a.png", Path(tmp) / "b.jpg"
            Image.new("RGB", (300, 300), "blue").save(source)
            size = compress_to_target(source, target, 250 * 1024)
            self.assertEqual(size, target.stat().st_size)
            self.assertLessEqual(size, 250 * 1024)

    def test_compression_rejects_tiny_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "a.png", Path(tmp) / "b.jpg"
            Image.new("RGB", (10, 10), "white").save(source)
            with self.assertRaises(ValueError):
                compress_to_target(source, target, 1000)


if __name__ == "__main__":
    unittest.main()
