
# coding: utf-8

# In[3]:

#Imports
import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import codecs
import csv
import re
import cerberus
import schema

OSM_FILE = "kerala_south.osm" 
SAMPLE_FILE = "sample.osm"
"""Path to new csv files"""
OSM_PATH = "kerala_south.osm"
NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"
""""Regular expression compilers"""
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
SCHEMA = schema.schema
"Fields of the new csv files"
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    poscounter = 0 #for way nodes position
    if element.tag == 'node':
        for field in NODE_FIELDS:
            node_attribs[field] = element.attrib[field]
        for tag in element.iter('tag'):
            tag_dict = {}
            tag_dict['id'] = element.attrib['id'] #id (NODE_TAGS_FIELDS)
            
            #key and type (NODE_TAGS_FIELDS)
            if PROBLEMCHARS.match(tag.attrib["k"]):
                pass
            elif ':' in tag.attrib['k']:
                tag_dict['type'] = tag.attrib['k'].split(':')[0]
                tag_dict['key'] = tag.attrib["k"].split(':',1)[1]
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = tag.attrib['k']
                
            #value (NODE_TAGS_FIELDS)
            tag_dict['value'] = tag.attrib['v']
            
            tags.append(tag_dict)
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        for field in WAY_FIELDS:
            way_attribs[field] = element.attrib[field]
        for nd in element.iter('nd'):
            nd_dict = {}
            nd_dict['id'] = element.attrib['id']
            nd_dict['node_id'] = nd.attrib['ref']
            nd_dict['position'] = poscounter
            poscounter += 1
            way_nodes.append(nd_dict)
        for tag in element.iter('tag'):
            if tag.attrib['k']=="addr:street" :
                """Calling update_name to update street names"""
                tag.attrib['v']=update_name(tag.attrib['v'],mapping)
            tag_dict = {}
            tag_dict['id'] = element.attrib['id'] #id
        for tag in element.iter('tag'):
            if tag.attrib['k']=="addr:postcode" :
                """Calling update_zip to update postal codes"""
                tag.attrib['v']=update_zip(tag.attrib['v'])
            #key and type
            if PROBLEMCHARS.match(tag.attrib["k"]):
                pass
            elif ':' in tag.attrib['k']:
                tag_dict['type'] = tag.attrib['k'].split(':')[0]
                tag_dict['key'] = tag.attrib["k"].split(':',1)[1]
            else:
                tag_dict['type'] = 'regular'
                tag_dict['key'] = tag.attrib['k']
            #value
            tag_dict['value'] = tag.attrib['v']
            
            tags.append(tag_dict)    
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
# HELPER FUNCTIONS    
    
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""
    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_strings = (
            "{0}: {1}".format(k, v if isinstance(v, str) else ", ".join(v))
            for k, v in errors.iteritems()
        )
        raise cerberus.ValidationError(
            message_string.format(field, "\n".join(error_strings))
        )
class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""
    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
# MAIN FUNCTION
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""
    with codecs.open(NODES_PATH, 'w') as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,codecs.open(WAYS_PATH, 'w') as ways_file,          codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:
        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()
        validator = cerberus.Validator()
        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])





process_map(OSM_PATH, validate=False)




import sqlite3



sqlite_file = 'kerala_south.db' 




conn = sqlite3.connect(sqlite_file)




"""Get a cursor object"""
cur = conn.cursor()




def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    """csv.py doesn't do Unicode; encode temporarily as UTF-8:"""
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]
def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
        
def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield {key: unicode(value, 'utf-8') for key, value in row.iteritems()}




# create nodes table
cur.execute("CREATE TABLE nodes (id, lat, lon, user, uid, version, changeset, timestamp);")
with open('nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) 
    to_db = [(i['id'], i['lat'], i['lon'], i['user'], i['uid'], i['version'], i['changeset'], i['timestamp'])              for i in dr]

cur.executemany("INSERT INTO nodes (id, lat, lon, user, uid, version, changeset, timestamp)                 VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db)
con.commit()

#create nodes_tags table
cur.execute("CREATE TABLE nodes_tags (id, key, value, type);")
with open('nodes_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) 
    to_db = [(i['id'], i['key'], i['value'], i['type']) for i in dr]

cur.executemany("INSERT INTO nodes_tags (id, key, value, type) VALUES (?, ?, ?, ?);", to_db)
con.commit()

#Create ways table
cur.execute("CREATE TABLE ways (id, user, uid, version, changeset, timestamp);")
with open('ways.csv','rb') as fin:
    dr = csv.DictReader(fin) 
    to_db = [(i['id'], i['user'], i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr]

cur.executemany("INSERT INTO ways (id, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?);", to_db)
con.commit()

#Create ways_nodes table
cur.execute("CREATE TABLE ways_nodes (id, node_id, position);")
with open('ways_nodes.csv','rb') as fin:
    dr = csv.DictReader(fin) 
    to_db = [(i['id'], i['node_id'], i['position']) for i in dr]

cur.executemany("INSERT INTO ways_nodes (id, node_id, position) VALUES (?, ?, ?);", to_db)
con.commit()

#Create ways_tags table
cur.execute("CREATE TABLE ways_tags (id, key, value, type);")
with open('ways_tags.csv','rb') as fin:
    dr = csv.DictReader(fin) 
    to_db = [(i['id'], i['key'], i['value'], i['type']) for i in dr]

cur.executemany("INSERT INTO ways_tags (id, key, value, type) VALUES (?, ?, ?, ?);", to_db)
con.commit()

"""Read in the csv file as a dictionary, format the
data as a list of tuples:"""
import pprint as pprint
with open('nodes_tags.csv','rb') as fin:
    dr = UnicodeDictReader(fin) 
    to_db = [(i['id'], i['key'],i['value'], i['type']) for i in dr]
with open('nodes.csv', 'rb') as fin2:
    dr2 = UnicodeDictReader(fin2)
    to_db2 = [(i['id'], i['lat'], i['lon'], i['user'], i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr2]
    
with open('ways.csv', 'rb') as fin3:
    dr3 = UnicodeDictReader(fin3)
    to_db3 = [(i['id'], i['user'], i['uid'], i['changeset'], i['timestamp']) for i in dr3]
    
with open('ways_tags.csv', 'rb') as fin4:
    dr4 = UnicodeDictReader(fin4)
    to_db4 = [(i['id'], i['key'], i['value'], i['type']) for i in dr4]  
    
with open('ways_nodes.csv', 'rb') as fin5:
    dr5 = UnicodeDictReader(fin5)
    to_db5 = [(i['id'], i['node_id'], i['position']) for i in dr5]  
    
# Insert the formatted data
cur.executemany("INSERT INTO nodes_tags(id, key, value,type) VALUES (?, ?, ?, ?);", to_db)
cur.executemany("INSERT INTO nodes(id, lat, lon, user, uid, version, changeset, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", to_db2)
cur.executemany("INSERT INTO ways(id, user, uid, changeset, timestamp) VALUES (?, ?, ?, ?, ?);", to_db3)
cur.executemany("INSERT INTO ways_tags(id, key, value, type) VALUES (?, ?, ?, ?);", to_db4)
cur.executemany("INSERT INTO ways_nodes(id, node_id, position) VALUES (?, ?, ?);", to_db5)
conn.commit()
cur.execute('SELECT * FROM nodes_tags')
all_rows = cur.fetchall()



conn.close()




#Counting number of nodes
conn = sqlite3.connect(sqlite_file)
cur = conn.cursor()
cur.execute('''
    SELECT COUNT(*) FROM nodes;
''')
all_rows = cur.fetchall()
print('Number of nodes are:{}').format(all_rows)
conn.commit()

# Counting number of ways

conn = sqlite3.connect(sqlite_file)

cur = conn.cursor()

cur.execute('''
    SELECT COUNT(*) FROM ways;
''')
all_rows = cur.fetchall()

print('Number of ways are:{}').format(all_rows)

conn.commit()
# Counting number of unique users

conn = sqlite3.connect(sqlite_file)

cur = conn.cursor()

cur.execute('''
SELECT COUNT(DISTINCT(e.uid))          
FROM (SELECT uid FROM nodes UNION ALL SELECT uid FROM ways) e;
''')

all_rows = cur.fetchall()

print('Number of unique users are:{}').format(all_rows)

conn.commit()
# TOP 10 contributing users

conn = sqlite3.connect(sqlite_file)

cur = conn.cursor()

cur.execute('''
SELECT e.user, COUNT(*) as num
FROM (SELECT user FROM nodes UNION ALL SELECT user FROM ways) e
GROUP BY e.user
ORDER BY num DESC
LIMIT 10;
''')

all_rows = cur.fetchall()

print('Top 10 contributing users are:{}').format(all_rows)


conn.commit()
# Biggest religion

conn = sqlite3.connect(sqlite_file)

cur = conn.cursor()

cur.execute('''
SELECT nodes_tags.value, COUNT(*) as num
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='place_of_worship') i
    ON nodes_tags.id=i.id
WHERE nodes_tags.key='religion'
GROUP BY nodes_tags.value
ORDER BY num DESC
LIMIT 1;
''')

all_rows = cur.fetchall()


print(all_rows)

conn.commit()
# Top 10 amenities

conn = sqlite3.connect(sqlite_file)

cur = conn.cursor()

cur.execute('''
SELECT value, COUNT(*) as num
FROM nodes_tags
WHERE key='amenity'
GROUP BY value
ORDER BY num DESC
LIMIT 10;
''')

all_rows = cur.fetchall()


print(all_rows)

conn.commit()
# Most popular cuisines


conn = sqlite3.connect(sqlite_file)

cur = conn.cursor()

cur.execute('''
SELECT nodes_tags.value, COUNT(*) as num
FROM nodes_tags 
    JOIN (SELECT DISTINCT(id) FROM nodes_tags WHERE value='restaurant') i
    ON nodes_tags.id=i.id
WHERE nodes_tags.key='cuisine'
GROUP BY nodes_tags.value
ORDER BY num DESC;
''')

all_rows = cur.fetchall()


print(all_rows)

conn.commit()






# In[ ]:



