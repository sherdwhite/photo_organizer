from exif import Image


def extract_exif_data(image_file):
    my_image = Image(image_file)
    if my_image.has_exif:
        datetime_original = (
            my_image.get("datetime_original")
            or my_image.get("media_created")
            or my_image.get("datetime_digitized")
        )
        return datetime_original
    return None
