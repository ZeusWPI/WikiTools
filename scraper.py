from urllib.request import urlopen
from urllib.error import URLError
from html.parser import HTMLParser
from os import fsync, path, makedirs
from datetime import date
from re import M, I, findall, search, compile


# This class parses the index page which contains hyperlinks to the wiki pages
class IndexPageParser(HTMLParser):
    def __init__(self, titles):
        super().__init__()
        self.titles = titles

    # Find the titles of the wiki pages
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if len(attrs) == 2
            and attrs[0][0] == 'href'
            and attrs[1][0] == 'title':
                self.titles.append(attrs[1][1])


class ImageLocater(HTMLParser):
    def __init__(self, imagelinks):
        super().__init__()
        self.imagelinks = imagelinks
        self.found = False
        self.data = ''
        # The regex to look for external image links in usercreated source code
        self.pattern = compile(r'\b((?:https?|ftp).*\.(?:png|jpe?g|gif|bmp))$',
                               M | I)

    # Look for the textarea in the html page
    def handle_starttag(self, tag, attrs):
        if tag == 'textarea':
            self.found = True

    # Now save the data within it
    def handle_data(self, data):
        if self.found:
            self.data += (data)

    def handle_endtag(self, tag):
        # This is executed for each tag so check if it's th right tag
        if tag == 'textarea':
            images = findall(self.pattern, self.data)
            if not images:
                print('\tNo images located!')
            else:
                print('\t%s' % images)
                for link in images:
                    self.imagelinks.append(link)
            self.found = False

INDEX_PAGE = 'http://zeus.ugent.be/wiki/Speciaal:AllePaginas'
SOURCE_LOCATION = 'http://zeus.ugent.be/wiki/index.php?title=%s&action=edit'
IMAGE_PATH = 'assets/'
KEYWORD = '/wiki/Speciaal:AllePaginas'
ENCODING = 'iso-8859_15'


def get_pages():
    # Download the index page containing hyperlinks to the other wiki pages
    print('Fetching source...')
    try:
        html = urlopen(INDEX_PAGE).read().decode(ENCODING)
    except:
        print("Unexpected exception while getting the indexpaga!")
        exit(1)
    if not html:
        print('Failed to fetch source!')
        exit(2)
    print('Source has been fetched!')

    # Narrow down the HTML
    html = str(html).split(KEYWORD)
    titles = []

    # Now find the titles in the narrowed down HTML
    parser = IndexPageParser(titles)
    parser.feed(html[1])
    # Never forget to close
    parser.close()

    create_directory()
    get_images(titles)


def create_directory():
    if not path.exists(IMAGE_PATH):
        makedirs(IMAGE_PATH)


def get_images(titles):
    h = HTMLParser()
    current_title = 0
    log_file = open(date.today()
                    .strftime('%Y-%m-%d %I-%M-%S%p') + '.log', 'wb')
    titles_length = len(titles)
    while current_title < titles_length:
        print('Fetching images from %s... (%s/%s)' %
              (titles[current_title], current_title + 1, titles_length))
        # Escape the title so we can create a valid link
        title = titles[current_title].replace('\'', '%27').replace(' ', '%20')
        try:
            page = urlopen(SOURCE_LOCATION % title)
            .read()
            .decode(ENCODING)
        except:
            print("\tServer's being lazy, retrying...")
            continue
        if not page:
            print('\tFailed to get %s\'s images!' % titles[current_title])
            current_title += 1
            continue
        # Ignore redirects
        if search('#DOORVERWIJZING', page, I | M) is not None or
        search('#REDIRECT.*', page, I | M) is not None:
            print('\tSkipping redirecting page %s' % titles[current_title])
            current_title += 1
            continue
        imagelinks = []
        parser = ImageLocater(imagelinks)

        page = h.unescape(page)
        parser.feed(page)
        parser.close()

        if imagelinks:
            # Log the title of the page
            log_file.write(bytes('%s\n' % title, ENCODING))
            for image_url in imagelinks:
                # Log the image url
                log_file.write(bytes('\t%s' % image_url, ENCODING))
                if not save_image(image_url):
                    log_file.write(bytes(' DEAD', ENCODING))
                log_file.write(bytes('\n', ENCODING))
            # Actually print something
            log_file.flush()
            fsync(log_file.fileno())
        current_title += 1
    log_file.close()


def save_image(image_url):
    if not path.exists(IMAGE_PATH + image_url.split('/')[-1]):
        try:
            image = urlopen(image_url)
            image_file = open(IMAGE_PATH + image_url.split('/')[-1], 'wb')
            image_file.write(image.read())
            image_file.close()
        except URLError:
            print('Dead link found: %s' % image_url)
            return False
    return True

if __name__ == '__main__':
    get_pages()
