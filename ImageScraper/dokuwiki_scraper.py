from urllib.error import URLError
from urllib.request import urlopen
from os import path, makedirs, walk
from re import M, I, findall, compile
from glob import glob

DATA_DIRECTORY = 'data'
MEDIA_DIRECTORY = '/media/'
MEDIA_SUBDIRECTORY = 'scraper'
PAGE_DIRECTORY = '/pages/'
IMAGE_PATTERN = compile(r'\b((?:https?|ftp).*\.(?:png|jpe?g|gif|bmp))', M | I)


def list_all_pages():
    page_paths = []  # List which will store all of the full filepaths.

    # Walk the tree.
    for root, directories, files in walk(DATA_DIRECTORY + PAGE_DIRECTORY):
        if 'pages/wiki' in root or 'pages/wikizeus' in root:
            continue  # skip these directories

        for filename in files:
            filepath = path.join(root, filename)
            page_paths.append(filepath)

    print(page_paths)

    return page_paths


def find_imagelinks_in_page(page_data):
    images = findall(IMAGE_PATTERN, page_data)
    if not images:
        print('\tNo images located!')
    else:
        print('\t%s' % images)

    return images


def page_name(page_path):
    return page_path.split('/')[-1].split('.')[0]


def fetch_and_write_image(image_url, image_save_path):
    image_path = str(DATA_DIRECTORY + MEDIA_DIRECTORY + MEDIA_SUBDIRECTORY + '/' + image_save_path)
    if not path.exists(image_path):
        try:
            image = urlopen(image_url)
            directory = path.dirname(image_path)
            if not path.isdir(directory):
                makedirs(directory)
            image_file = open(image_path, 'wb')
            image_file.write(image.read())
            image_file.close()
        except URLError:
            print('Dead link found: %s' % image_url)
            return False
    return True


def test_if_images_already_exist_for_page(name):
    image_path = str(DATA_DIRECTORY + MEDIA_DIRECTORY + MEDIA_SUBDIRECTORY + '/' + name + '*')
    number = 0
    for name in glob(image_path):
        new_number = int(name.split('-')[-1].split('.')[0])
        number = max(number, new_number)
    return number


def handle_pages():
    page_list = list_all_pages()

    for page in page_list:
        name = page_name(page)
        print('Reading %s' % name)
        with open(page, "r+") as page_file:
            page_data = str(page_file.read())
            modified = False
            imagelinks = find_imagelinks_in_page(page_data)
            start = test_if_images_already_exist_for_page(name)
            for count, image in enumerate(imagelinks):
                image_name = '%s-%d.%s' % (name, count+1+start, image.split('.')[-1])
                if fetch_and_write_image(image, image_name):
                    page_data = page_data.replace(image, MEDIA_SUBDIRECTORY + ':' + image_name)
                    modified = True

            if modified:
                # write to file
                page_file.seek(0)
                page_file.write(page_data)
                page_file.truncate()
                print('%s updated' % name)

if __name__ == '__main__':
    handle_pages()
