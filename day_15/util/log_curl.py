import aiohttp
from urllib.parse import urlencode

async def log_curl_request(session, trace_config):
    def convert_headers(headers):
        return ' \\\n  -H "' + '" \\\n  -H "'.join(
            f'{k}: {v}' for k, v in headers.items()
        ) + '"'

    async def on_request(request, traces):
        url = request.url
        method = request.method
        headers = dict(request.headers)
        
        curl_cmd = f'curl -X {method} "{url}'
        if request.headers:
            curl_cmd += f'\n  {convert_headers(headers)}'
        if request.data:
            if isinstance(request.data, str):
                curl_cmd += f'\n  -d "{request.data}"'
            else:
                curl_cmd += f'\n  -d "{urlencode(request.data)}"'
        
        print(curl_cmd)
    
    trace_config.on_request_start.append(on_request)
