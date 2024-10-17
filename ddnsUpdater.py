import os
import requests
from dotenv import load_dotenv

def postDiscordWebhook(discordWebhookUri: str, exception: Exception = None, description: str = None) -> str:
    if discordWebhookUri == '':
        return None
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    body = { "content": f"Description: {description} "}
    
    if exception != None:
        body = '{ "content": "Exception: ' + exception + '\nDescription: ' + description + '" }'

    try:
        response = requests.post(url=discordWebhookUri, headers=headers, json=body)        
    except Exception as ex:
        return ex

    return response.status_code

def splitEqualsToDict(data: str) -> dict:
    if data.find('\n') != -1:
        data = data.split('\n')

    result = {}
    for line in data:
        if line == '':
            break
        key, value = line.split('=', 1)
        result[key] = value
    
    return result

def getPublicIPv4(discordWebhookUri: str) -> str:
    try:
        response = requests.get("https://cloudflare.com/cdn-cgi/trace")
        responseDict = splitEqualsToDict(response.text)
        ip = responseDict['ip']

    except Exception as ex:
        try:
            postDiscordWebhook(discordWebhookUri, exception = ex)
            ip = requests.get('https://api.ipify.org').text

        except Exception as ex:
            try:
                postDiscordWebhook(discordWebhookUri, exception = ex)
                ip = requests.get('https://ipv4.icanhazip.com').text

            except Exception as ex:
                postDiscordWebhook(discordWebhookUri, exception = ex)
                ip = 0

    return ip


if __name__ == '__main__':
    
    # Load .env file
    load_dotenv()
    cloudflareEmail   = os.getenv('CF_EMAIL')
    authMethod        = os.getenv('AUTH_METHOD')
    apiKey            = os.getenv('API_KEY')
    zoneIdentifier    = os.getenv('ZONE_IDENTIFIER')
    recordName        = os.getenv('RECORD_NAME')
    ttl               = os.getenv('TTL')
    proxy             = os.getenv('PROXY')
    discordWebhookUri = os.getenv('DISCORD_URI')
    
    ip = getPublicIPv4(discordWebhookUri)

    if ip == 0:
        postDiscordWebhook(discordWebhookUri, description="IP nula")

    print(ip)
    
    postDiscordWebhook(discordWebhookUri, description=f"<@275651418353041408>\nUpdated IP address for: {recordName}")