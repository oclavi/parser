import os, ssl, json
from urllib.request import urlopen
from urllib.parse import urlencode

def _api_url(email, project_id, token, storage_type):
    api_url = 'https://app.oclavi.com/oapi/apiexport?'
    query_params = urlencode({'email':email, 'projectId':project_id, 'token': token, 'activeStorage': storage_type})
    return str(api_url + query_params)

def _get_json(api_url, object_hook=None):
    """Returns the json from url"""
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)):
        ssl._create_default_https_context = ssl._create_unverified_context
    with urlopen(api_url) as resource:
        return json.load(resource, object_hook=object_hook)

def _get_json_from_file(file_path):
    """Returns the json file data"""
    with open(file_path) as f:
        return json.load(f)

def _get_model_spec_output(model_schema, label, image):
    """Returns the parsed output for a particular label from OCLAVI"""

    output_dict = {}
    for key, val in model_schema["SCHEMA"].items():
        if type(val) == dict:
            if model_schema["DATA_TYPE"][key] == 'list' and "EDGES_RECT" in val["to_check"]:
                if val["to_check"] in label:
                    val_list = val["to_get"].split(", ") if ", " in val["to_get"] else val["to_get"]
                    for i, s in enumerate(val_list):
                        if "$." in s:
                            val_list[i] = s.replace('$.', '')
                            val_key = val_list[i].split(".") if "." in val_list[i] else val_list[i]
                            for each_annotation in label[val_key[0]]:
                                if key in output_dict.keys():
                                    output_dict[key].append(each_annotation[val_key[1]])
                                else:
                                    output_dict[key] = [each_annotation[val_key[1]]]
            elif model_schema["DATA_TYPE"][key] == 'list' and "EDGES_POLY" in val["to_check"]:
                if val["to_check"] in label:
                    val_list = val["to_get"].split(".")
                    val_list.remove("$")
                    ls = "['" + "']['".join(val_list) + "']"
                    for each_annotation in label[ls]:
                        if eval(ls.replace('[', '').replace(']','')) in label:
                            output_dict[key] = each_annotation[eval(ls.replace('[', '').replace(']',''))]
            else:
                val_list = val["to_get"].split(".") if "." in val["to_get"] else val["to_get"]
                if "$" in val_list:
                    val_list.remove("$")
                    ls = "['" + "']['".join(val_list) + "']"
                    if eval(ls.replace('[', '').replace(']','')) in label:
                        output_dict[key] = label[eval(ls.replace('[', '').replace(']',''))]
                    else:
                        break
                else:
                    output_dict[key] = image[val]
        else:
            output_dict[key] = image[val]
    return output_dict

    
def _parser(model_name, email, project_id, token, storage_type):
    """Returns the parsed output based on model schema"""

    # Get the root path
    root_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))

    _json_datum = _get_json(_api_url(email, project_id, token, storage_type))
    # _json_datum = _get_json_from_file(os.path.join(root_path, 'apiexport.json'))

    #Read the settings
    _settings_datum = _get_json_from_file(os.path.join(root_path, 'settings.json'))

    # Get the model schema
    if str(model_name) in _settings_datum["MODEL_NAMES"]:
        _model_schema = _get_json_from_file(os.path.join(root_path, model_name + '.json'))
        
        _parsed_output = []
        for each_image in _json_datum:
            for each_label in each_image["LABEL_DETAILS"]:
                _parsed_output.append(_get_model_spec_output(_model_schema, each_label, each_image))
    return _parsed_output