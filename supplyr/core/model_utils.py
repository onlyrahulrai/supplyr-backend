import os
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

def generate_image_sizes(instance, field_name, schema, save = True):
    print("GENERATING SCHEMA")
    image_field = getattr(instance, field_name)
    
    original_image = Image.open(image_field)
    ext = os.path.splitext(image_field.path)[1]

    if ext in [".jpg", ".jpeg"]:
        PIL_TYPE = 'JPEG'
        FILE_EXTENSION = 'jpg'

    elif ext == ".png":
        PIL_TYPE = 'PNG'
        FILE_EXTENSION = 'png'

    if original_image.mode not in ('L', 'RGB'):
        original_image = original_image.convert('RGB')

    for image_variant in schema:
        field = getattr(instance, image_variant['field_name'])
        new_image = original_image.copy()
        new_image.thumbnail(image_variant['size'], Image.ANTIALIAS)
        fp = BytesIO()
        new_image.save(fp, PIL_TYPE, quality=image_variant['quality'])
        cf = ContentFile(fp.getvalue())
        field.save('only_ext_is_relevant.' + FILE_EXTENSION, content = cf, save = False)

    if save:
        instance.save()
    # return instance # Not really needed, the instance will get updated through reference