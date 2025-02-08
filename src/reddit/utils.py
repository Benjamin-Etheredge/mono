import requests
from praw.models import Submission


def download_image_urls(image_urls):
    temp_names = []

    for idx, image_url in enumerate(image_urls):
        response = requests.get(image_url)
        if "jpg" not in image_url and "jpeg" not in image_url:
            continue
        # TODO handle tmp file better
        temp_names.append(f"/tmp/{idx}.jpg")
        # try:
        #     with Image.open(response.content) as img:  # Open the image using PIL.
        #         assert img.format == "JPEG"
        #         img.verify()  # Verify that it is, indeed an image.
        # except Exception as e:
        #     print(f"Invalid image at index {idx}: {e}")
        #     continue  # Skip this image if it's invalid.

        with open(temp_names[-1], "wb") as f:
            f.write(response.content)
    return temp_names


def get_images(submission: Submission):
    image_urls = []
    try:
        ids = [item["media_id"] for item in submission.gallery_data["items"]]
        for id in ids:
            url = submission.media_metadata[id]["p"][0]["u"]
            url = url.split("?")[0].replace("preview", "i")
            image_urls.append(url)
    except AttributeError:
        print("not gallery...")
        # Assume just a single image
        image_urls.append(submission.url)
    return image_urls
