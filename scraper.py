from urllib.request import urlopen
from html.parser import HTMLParser
from os import fsync, path, makedirs
from datetime import date
from re import M, I, findall, search, compile

class MainPageParser(HTMLParser):
    def __init__(self, titles):
        super().__init__()
        self.titles = titles

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            if len(attrs) == 2 and attrs[0][0] == 'href' and attrs[1][0] == 'title':
                self.titles.append(attrs[1][1])

class ImageLocater(HTMLParser):
    def __init__(self, imagelinks):
        super().__init__()
        self.imagelinks = imagelinks
        self.gotcha = False
        self.data = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'textarea':
            self.gotcha = True

    def handle_data(self, data):
        if self.gotcha:
            self.data += (data)

    def handle_endtag(self, tag):
        if tag == 'textarea':
            pattern = compile(r'\b((?:https?|ftp).*\.(?:png|jpe?g|gif|bmp))$', M | I)
            images = findall(pattern, self.data)
            if not images:
                print('\tNo images located!')
            else:
                print('\t%s' % images)
                for link in images:
                    self.imagelinks.append(link)
            self.gotcha = False

SOURCE = 'http://zeus.ugent.be/wiki/Speciaal:AllePaginas'
BASE = 'http://zeus.ugent.be/wiki/index.php?title=%s&action=edit'
IMAGE_PATH = 'images/'
KEYWORD = '/wiki/Speciaal:AllePaginas'

def get_pages():
    print('Fetching source...')
    try:
        html = urlopen(SOURCE).read().decode('iso-8859_15')
    except:
        print("Unexpected exception while getting the mainpage!")
        exit(1)
    if not html:
        print('Failed to get source!')
        exit(2)
    print('Source was captured!')
    html = str(html).split(KEYWORD)
    titles = []
    parser = MainPageParser(titles)
    parser.feed(html[1])

    create_directory()
    get_images(titles)
    parser.close()

def create_directory():
    if not path.exists(IMAGE_PATH):
        makedirs(IMAGE_PATH)

def save_image(image):
    if not path.exists(IMAGE_PATH + image.split('/')[-1]):
        try:
            u = urlopen(image)
            imagefile = open(IMAGE_PATH + image.split('/')[-1], 'wb')
            imagefile.write(u.read())
            imagefile.close()
        except URLError:
            print('Dead link found: %s' % image)
            return False
    return True

def get_images(titles):
    i = 0
    f = open(date.today().strftime('%Y-%m-%d %I-%M-%S%p') + '.log', 'wb')
    titleslen = len(titles)
    while i < titleslen:
        print('Fetching images from %s... (%s/%s)' % (titles[i], i + 1, titleslen))
        htmltitle = titles[i].replace('\'','%27').replace(' ', '%20')
        try:
            page = urlopen(BASE % htmltitle).read().decode('iso-8859_15')
        except:
            print("\tServer's being lazy, retrying...")
            continue
        if not page:
            print('\tFailed to get %s\'s images!' % titles[i])
            i += 1
            continue
        if search('#DOORVERWIJZING', page, I | M) != None or search('#REDIRECT.*', page, I | M) != None:
            print('\tSkipping redirecting page %s' % titles[i])
            i += 1
            continue
        imagelinks = []
        parser = ImageLocater(imagelinks)
        page = page.replace('&lt;','<').replace('&gt;','>').replace('&quot;', '"').replace('&amp;', '&')
        parser.feed(page)
        parser.close()
        if imagelinks:
            f.write(bytes('%s\n' % htmltitle, 'iso-8859_15'))
            for image in imagelinks:
                f.write(bytes('\t%s' % image, 'iso-8859_15'))
                if not save_image(image):
                    f.write(bytes(' DEAD', 'iso-8859_15'))
                f.write(bytes('\n', 'iso-8859_15'))
            f.flush()
            fsync(f.fileno())
        i += 1
    f.close()

if __name__ == '__main__':
    get_pages()