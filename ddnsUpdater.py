import os
import requests
from dotenv import load_dotenv

def postDiscordWebhook(discordWebhookUri: str, exception: Exception = None, description: str = None) -> requests.status_codes:
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


def findRecordOnCloudflare(cloudflareURL, zoneIdentifier, cloudflareEmail, authMethod, apiKey, recordName) -> str:
    if authMethod == 'global':
        authMethodTag = "X-Auth-Key:"
    else:
        authMethodTag = "Authorization"
        apiKey = "Bearer " + apiKey

    headers = {
        'X-Auth-Email': cloudflareEmail,
        authMethodTag: apiKey,
        'Content-Type': 'application/json'
    }

    url = cloudflareURL + zoneIdentifier + '/dns_records?type=A&name=' + recordName

    try:
        response = requests.get(url=url, headers=headers)    
    except Exception as ex:
        return ex
    
    if response.json()['result_info']['count'] == 0:
        return None
    
    return response.json()['result'][0]['content']

def main():
    
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
    discordUserID     = os.getenv('DISCORD_USER_ID')

    #Params
    cloudflareURL = 'https://api.cloudflare.com/client/v4/zones/'
    

    ip = getPublicIPv4(discordWebhookUri)
    
    if ip == 0:
        postDiscordWebhook(discordWebhookUri, description="IP nula")

    recordIP = findRecordOnCloudflare(cloudflareURL, zoneIdentifier, cloudflareEmail, authMethod, apiKey, recordName)

    if recordIP == None:
        postDiscordWebhook(discordWebhookUri, description=f"Record \"{recordName}\" not found.\n{discordUserID}")
        return None
    
    if ip == recordIP:
        postDiscordWebhook(discordWebhookUri, description=f"The ip hasn\'t changed for the Record: {recordName}")
        return None

    postDiscordWebhook(discordWebhookUri, description=f"Updated IP address for: {recordName}\n{discordUserID}")


#Program start
if __name__ == '__main__':
    main()