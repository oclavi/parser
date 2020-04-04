from parser import _parser

try:
    _parser('coco', 'email@email.com', 'project_id', 'api_token', 'GOOGLE_DRIVE')
except Exception as e:
    print (e)