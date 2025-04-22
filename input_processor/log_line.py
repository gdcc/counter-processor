import config
import re
from models import *
from urllib.parse import urlparse
import geoip2.errors

class LogLine():
    """A class to handle log line importing from log to database"""

    # the columns from the report in this order
    COLUMNS = ('event_time', 'client_ip', 'session_cookie_id', 'user_cookie_id', 'user_id', 'request_url', 'identifier',
        'filename', 'size', 'user_agent', 'title', 'publisher', 'publisher_id', 'authors', 'publication_date', 'version',
        'other_id', 'target_url', 'publication_year')
    # required columns that can NOT be empty
    REQUIRED = {'event_time', 'identifier'}
    ROBOTS_REGEX = re.compile(config.Config().robots_regexp())
    MACHINES_REGEX = re.compile(config.Config().machines_regexp())

    __slots__ = ('badline',) + COLUMNS

    def __init__(self, line):
        self.badline = False
        line = line.strip()
        if line.startswith('#'):
            self.badline = True
            return

        split_line = line.strip().split("\t")
        if len(split_line) != len(self.COLUMNS):
            print(f'line is wrong: {line}')
            self.badline = True
            return

        # import the COLUMNS above
        for idx, field in enumerate(self.COLUMNS):
            value = split_line[idx].strip()
            if value in ('', '-', '????'):
                value = None
                if field in self.REQUIRED:
                    self.badline = True
                    print(f'Required field is missing : {field} : {line}')
                    return
            self.__setattr__(field, value)

    def populate(self):
        if self.badline == True:
            return

        # create descriptive metadata
        md_item = self.find_or_create_metadata()

        # add base logging data
        l_item = LogItem()
        for my_field in self.COLUMNS[0:10]:
            setattr(l_item, my_field, getattr(self, my_field))

        l_item.is_robot = self.is_robot()
        # no point saving this log line since we ignore "is_robot" logs in the report
        if l_item.is_robot:
            return

        l_item.country = self.lookup_geoip()
        l_item.hit_type = self.get_hit_type()
        l_item.is_machine = self.is_machine()

        # link-in descriptive metadata
        l_item.metadata_item = md_item.id

        # add COUNTER style user-session identification for double-click detection
        l_item.add_doubleclick_id()

        # add COUNTER style session tracking with timeslices and different types of tracking
        l_item.add_session_id()

        # save the basic log record
        l_item.save()

        # remove previous duplicates within 30 seconds
        l_item.de_double_click()


    def find_or_create_metadata(self):
        with DbActions._meta.database.atomic():
            mi, created = MetadataItem.get_or_create(
                identifier=self.identifier,
                defaults={
                    'title': self.title,
                    'publisher': self.publisher,
                    'publisher_id': self.publisher_id,
                    'publication_date': self.publication_date,
                    'version': self.version,
                    'other_id': self.other_id,
                    'target_url': self.target_url,
                    'publication_year': self.publication_year
                }
            )
            if created:
                self.create_authors(md_item=mi)
        return mi

    def create_authors(self, md_item):
        with DbActions._meta.database.atomic():
            MetadataAuthor.delete().where(MetadataAuthor.metadata_item_id == md_item.id).execute()

            if self.authors is None:
                MetadataAuthor.create(metadata_item_id=md_item.id, author_name="None None")
            else:
                authors = [{'metadata_item_id': md_item.id, 'author_name': au} for au in self.authors.split("|")]
                MetadataAuthor.insert_many(authors).execute()

    def lookup_geoip(self):
        """Lookup the geographical area from the IP address and return the 2 letter code"""
        # try to grab this IP location cached in our existing database when possible to cut down on possible API requests
        prev = LogItem.select().where(LogItem.client_ip == self.client_ip).limit(1)
        for l in prev:
            return l.country

        try:
            response = config.Config().geoip_reader.country(self.client_ip)
            isocode = response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            isocode = None
        return isocode

    def get_hit_type(self):
        o = urlparse(self.request_url)
        hit_types = config.Config().hit_type_regexp()
        for k, v in hit_types.items():
            if v.search(o.path):
                return k
        return None

    def is_robot(self):
        return bool(self.user_agent and self.ROBOTS_REGEX.search(self.user_agent))

    def is_machine(self):
        return not self.user_agent or bool(self.MACHINES_REGEX.search(self.user_agent))
