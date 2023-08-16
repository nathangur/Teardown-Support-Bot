import json
import re

def parse_lua_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    functions = re.findall(r'---(.*?)function\s+(.*?)\(', content, re.DOTALL)
    result = {'version': '1.3.0', 'functions': []}
    for func in functions:
        docstring = func[0].strip().replace('---', '').replace('\n', '').replace('\t', '')
        description = re.search(r'(.*?)(?=@param|@return|$)', docstring).group(1).strip()
        description = '\n'.join([description[i:i+80] for i in range(0, len(description), 80)])
        params = re.findall(r'@param\s+(.*?)(?=@param|@return|$)', docstring)
        returns = re.findall(r'@return\s+(.*?)(?=@param|@return|$)', docstring)
        arguments = []
        for param in params:
            param_parts = param.split(' ')
            arguments.append({
                'name': param_parts[0],
                'desc': ' '.join(param_parts[1:]),
                'optional': False,
                'type': 'unknown'
            })
        returns_list = []
        for ret in returns:
            returns_list.append({
                'name': '',
                'desc': ret,
                'optional': False,
                'type': 'unknown'
            })
        result['functions'].append({
            'name': func[1].strip(),
            'description': description,
            'arguments': arguments if arguments else [{'name': '', 'desc': '', 'optional': False, 'type': ''}],
            'returns': returns_list if returns_list else [{'name': '', 'desc': '', 'optional': False, 'type': ''}],
            'examples': [],
            'tables': {}
        })
    with open('output.json', 'w') as f:
        json.dump(result, f, indent=4)

parse_lua_file('Automatic.lua')