
# coding: utf-8

# In[1]:

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
k = 10 # Parameter: take every k-th top level element

def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')
    
  
def count_tags(filename):
    dict_ = {}
    for event,elem in ET.iterparse(filename):
        if elem.tag not in dict_:
            dict_[elem.tag] = 1
        else:
            dict_[elem.tag] += 1
    return dict_


tags = count_tags(OSM_FILE)
#tags = count_tags(SAMPLE_FILE)
pprint.pprint(tags)

#Finding count for each of the four tag categories
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')



def key_type(element, keys):
    if element.tag == "tag":
        for tag in element.iter('tag'):
            k = tag.get('k')
            if lower.search(element.attrib['k']):
                keys['lower'] = keys['lower'] + 1
            elif lower_colon.search(element.attrib['k']):
                keys['lower_colon'] = keys['lower_colon'] + 1
            elif problemchars.search(element.attrib['k']):
                keys['problemchars'] = keys['problemchars'] + 1
            else:
                keys['other'] = keys['other'] + 1
    
    return keys

def write_data(data, filename):
    with open(filename, 'wb') as f:
        for x in data:
            f.write(x + "\n")


def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

pprint.pprint(process_map(OSM_FILE))
#pprint.pprint(process_map(SAMPLE_FILE))
#audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix the unexpected 
#street types to the appropriate ones in the expected list.
regex = re.compile(r'\b\S+\.?', re.IGNORECASE)
expected =["Road","Street","Lane","Kollam","Ernakulam","Thiruvananthapuram","Kerala","Nagar","Junction"]
mapping={"road":"Road",
        "rd":"Road",
        "Rd":"Road",
         "Jn":"Junction",
         "jun":"Junction",
         "Allapura":"Alappuzha",
         "Opp.":"Opposite",
         "Colany":"Colony",
         "Oppo:":"Opposite",
         "Rd,":"Road",
         "junctin":"Junction",
         "Allapuzha":"Alappuzha",
         "VII" :"Seventh",
         "TV Puram":"Thiruvananthapuram"
         
        }
# Search string for the regex. If it is matched and not in the expected list then add this as a key to the set.
def audit_street(street_types, street_name): 
    m = regex.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street_name(elem): # Check if it is a street name
    return (elem.attrib['k'] == "addr:street")

def audit(osmfile): # return the list that satify the above two functions
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street(street_types, tag.attrib['v'])

    return street_types

#pprint.pprint(dict(audit(SAMPLE_FILE))) # print the existing names
pprint.pprint(dict(audit(OSM_FILE)))
def string_case(s): # change string into titleCase except for UpperCase
    if s.isupper():
        return s
    else:
        return s.title()
# return the updated names
def update_name(name, mapping):
    name = name.split(' ')
    for i in range(len(name)):
        if name[i] in mapping:
            name[i] = mapping[name[i]]
            name[i] = string_case(name[i])
        else:
            name[i] = string_case(name[i])
    
    name = ' '.join(name)
   

    return name

#update_street = audit(SAMPLE_FILE) 
update_street = audit(OSM_FILE) 

# print the updated names
for street_type, ways in update_street.iteritems():
    for name in ways:
        better_name = update_name(name, mapping)
        print name, "=>", better_name  


# In[3]:

#Auditing postal codes
filename = open("kerala_south.osm", "r")
zip_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

zip_types = defaultdict(set)

expected_zip = {}

def audit_zip_codes(zip_types, zip_name, regex, expected_zip):
    m = regex.search(zip_name)
    if m:
        zip_type = m.group()
        if zip_type not in expected_zip:
             zip_types[zip_type].add(zip_name)
def is_zip_name(elem):
    return (elem.attrib['k'] == "addr:postcode")


def audit(filename, regex):
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "way" or elem.tag == "node":
            for tag in elem.iter("tag"):
                if is_zip_name(tag):
                    audit_zip_codes(zip_types, tag.attrib['v'], regex, expected_zip)
    pprint.pprint(dict(zip_types))
audit(filename, zip_type_re)
def update_zip(name):
    groups = re.findall(r'^(\d{3})(\d{3])$', name)[0]
    cleaned_postalcode = ' '.join(groups)
    return cleaned_postalcode



# In[ ]:



