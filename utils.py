from collections import namedtuple
import keyword

def make_object_from_dict(update_dict: dict, type_name: str):
    if not issubclass(type(update_dict), dict):
        return update_dict
    for k, v in update_dict.items():
        if issubclass(type(v), dict):
            update_dict[k] = make_object_from_dict(v, type_name=str(k))

    field_names = list(map(lambda x: x + '_' if keyword.iskeyword(x) else x, update_dict.keys()))
    if keyword.iskeyword(type_name):
        type_name = type_name + '_'
    return namedtuple(type_name, field_names)(*update_dict.values())
