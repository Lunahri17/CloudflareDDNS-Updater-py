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
        body = { "content": f"Exception: {str(exception)}\nDescription: {description}" }

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

def setHeadersCloudflare(cloudflareEmail: str, authMethod: str, apiKey: str) -> dict:
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

    return headers

def getRecordOnCloudflare(cloudflareURL: str, zoneIdentifier: str, headers: dict, recordName: str) -> str:
    url = cloudflareURL + zoneIdentifier + '/dns_records?type=A&name=' + recordName

    try:
        response = requests.get(url=url, headers=headers)
    except Exception as ex:
        return ex, "ex"
    
    if response.json()['result_info']['count'] == 0:
        return None, None
    
    return response.json()['result'][0]['content'], response.json()['result'][0]['id']

def updateRecordIPCloudflare(cloudflareURL: str, zoneIdentifier: str, recordID: str, headers: dict, recordName: str, ip: str, ttl: str, proxy: str) -> str:
    url = cloudflareURL + zoneIdentifier + '/dns_records/' + recordID

    body = {
        "type": "A",
        "name": recordName,
        "content": ip,
        "ttl": int(ttl),
        "proxied": bool(proxy)
    }

    try:
        response = requests.patch(url=url, headers=headers, json=body)
    except Exception as ex:
        return {
            "success": "ex",
            "exception": ex
        }

    return response.json()

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
    headers = setHeadersCloudflare(cloudflareEmail, authMethod, apiKey)

    #Get Public IP
    ip = getPublicIPv4(discordWebhookUri)
    
    if ip == 0:
        postDiscordWebhook(discordWebhookUri, description="IP nula")

    #use a local way to compare the ip, maybe use a env tag to disable this

    #Get RecordID and RecordIP from Cloudflare
    recordIP, recordID = getRecordOnCloudflare(cloudflareURL, zoneIdentifier, headers, recordName)

    if recordID == "ex":
        postDiscordWebhook(discordWebhookUri, description=f"Failed to connecto to Cloudflare, Abort.\n{discordUserID}", exception=recordIP)
        return None
    
    if recordIP == None:
        postDiscordWebhook(discordWebhookUri, description=f"Record \"{recordName}\" not found.\n{discordUserID}")
        return None
    
    if ip == recordIP:
        postDiscordWebhook(discordWebhookUri, description=f"The ip hasn\'t changed for the Record: {recordName}")
        return None
    

    #Update IP for the CloudFlare Record
    response = updateRecordIPCloudflare(cloudflareURL, zoneIdentifier, recordID, headers, recordName, ip, ttl, proxy)
    
    if response['success'] == "ex":
        postDiscordWebhook(discordWebhookUri, exception=response['exception'],description=f'Error al actualizar el record.\n{discordUserID}')
        return None

    if response['success'] == False:
        postDiscordWebhook(discordWebhookUri, description=f'Error al actualizar el record.\nError: {response['errors'][0]['message']}\n{discordUserID}')
        return None
    
    postDiscordWebhook(discordWebhookUri, description=f"Updated IP address for: {recordName}\n{discordUserID}")


#Program start
if __name__ == '__main__':
    main()