from json import JSONDecoder, JSONDecodeError
import re


# returns a generator which seperates the json objects in file
def decode_stacked(document, pos=0, decoder=JSONDecoder()):

    NOT_WHITESPACE = re.compile(r'[^\s]')
    while True:
        match = NOT_WHITESPACE.search(document, pos)
        if not match:
            return
        pos = match.start()

        try:
            obj, pos = decoder.raw_decode(document, pos)
        except JSONDecodeError:
            # do something sensible if there's some error
            raise
        yield obj


# returns a list with json objects, each object corresponds to bgp
# configuration of each router with which artemis is connected
def read_json_file(filename):

    json_data = []
    with open(filename) as json_file:
        json_stacked_data = json_file.read()
        for obj in decode_stacked(json_stacked_data):
            json_data.append(obj)

    return json_data


if __name__ == '__main__':
    json_data = read_json_file('../bgp_config_files/results.json')
    ### just for debugging ###
    with open('file.txt') as file:
        file.write(json_data)