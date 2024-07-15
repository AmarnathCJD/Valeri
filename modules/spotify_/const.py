from requests import get
import logging

log = logging.getLogger('spotify - auth')

DEVICE_WVD = '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zrdi1gc0WhHotJPZfIp0Qx4wVkDd4EaTQa2MVxfyR2gb++Vh8kXj71ZCEz5PFdYNnVsGkaofvjP1tJN6oXvCQi6/AQ4HwZu8wxroHEfhvJIPXOY6Rtvwiyixbe5C0OeyflbNoRmugacu6jOj1F0+3zZGhcCFl9bMJr2kB1cylgNZ9YOKcGU4myIqLblH1brFQ7gatAUKrgIIARIQaePomLssP7ijsygdhPiMFBiO1b6RBSKOAjCCAQoCggEBANj26bWJ8FEg6aQ+0NlOof4JlQFtvR4rQKfc0cV/wwVQPM8TP56Yr85O5v+E3EIkJqj/+k/kvy1E1Q8UOuu8IEyjtGf6JRv6YD/bJeInqK+pw30K72Lmo5TXKCif1JZlGy6MUUHyfFWt5jkvN6rTbzfOfUKDWy1xfi04dPu60/MUb9F4MVC3Q78YuXNXAHR3WyfdIow7hcuOFl2dyu0X2OWOmDvGMwiWdYlSrEOjtNCRPK0mZSXSRwztud0Et6sB0kUZpdzqhJjh43L8gYOW4sJBHcpkRCzL+Yt5XWCBDjgwWvtc4z6t37j/fXir915BuMeqNYW5WvyIhopur5HrdKECAwEAASjwIhKAAyKLYzDrP5CzVu+/EZK2J722lyCg7a4C3lm+/QINe+sWXCdJuj6pHvVG7YiVlZVJs3ldhIgPBzAHMeNjys2vd+Cxe1Im3Ljbl2M1C0Xn4naOsCF/dDabsQjlqiFkakPYTRyv51WP2jzHS4lHY1ZHwVWhVBJdmlp3cz/hDMEs22j+3P5QrJnBrtJz95NBzb5lwNLdkQ7eUZGwfzrgp/9wQa8lEEGpyklcp8b4i2oRbUAA+m2O6CDOZkTNGrnFMZ/qiv5tesqMKkFL0bVI7K8I0XWTnPqUbwqxeGBDEvoAMcyi6XG9QiKHI9jkymKZ1d9R0RDkcDYSo2I1U0g7io/TTuNbnXIB5OE6vLgnbbGzxF2QgKU4YBq4siXSUsDh+UzNb5V9CXnFjE/QTm26GfSH7zjgOyVTxkXtTV1TZCmsgCl99cP3CAAAKTbpGCDLx73rPyLzr/5hjJlCRz2Eh0IARGuARgIRsHLM42t1EOzUytL9yHWahXmkm/rcEgq9Aca8uRoWCgxjb21wYW55X25hbWUSBkdvb2dsZRonCgptb2RlbF9uYW1lEhlBbmRyb2lkIFNESyBidWlsdCBmb3IgeDg2GhgKEWFyY2hpdGVjdHVyZV9uYW1lEgN4ODYaGgoLZGV2aWNlX25hbWUSC2dlbmVyaWNfeDg2Gh4KDHByb2R1Y3RfbmFtZRIOc2RrX2dwaG9uZV94ODYaXwoKYnVpbGRfaW5mbxJRZ29vZ2xlL3Nka19ncGhvbmVfeDg2L2dlbmVyaWNfeDg2OjguMS4wL09TTTEuMTgwMjAxLjAwNy80NTg2NjQ2OnVzZXIvcmVsZWFzZS1rZXlzGi0KCWRldmljZV9pZBIgTWxCWFJDV2FtbmpXZXlwbVVWd2xCeXhKT3lnQkxIYgAaJgoUd2lkZXZpbmVfY2RtX3ZlcnNpb24SDnY1LjEuMC1hbmRyb2lkGiQKH29lbV9jcnlwdG9fc2VjdXJpdHlfcGF0Y2hfbGV2ZWwSATAyDBABIAAoDTAAQABIAA=='

AUDIO_LICENSE_URL = 'https://gew1-spclient.spotify.com/widevine-license/v1/audio/license'

DEFAULT_QUALITY = 'OGG_VORBIS_320'

def refresh_token(sp_c: str) -> str:
        if not sp_c:
            print('Error: Please provide a Spotify "sp_dc" cookie. (set env "SPOTIFY_DC")')
            exit(1)
            
        log.info('refreshing spotify access token')
    
        url = 'https://open.spotify.com/get_access_token'
        params = {
            'reason': 'transport',
            'productType': 'web-player'
        }
        request = get(url, headers={
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en',
            'App-Platform': 'WebPlayer',
            'Connection': 'keep-alive',
            'Cookie': f'sp_dc={sp_c}',
            'Host': 'open.spotify.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Spotify-App-Version': '1.2.33.0-unknown',
            'TE': 'trailers',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
        }, params=params)
        request.raise_for_status()
        json = request.json()
        is_anonymous = json['isAnonymous']
        if is_anonymous:
            print('Error: Please use a valid Spotify "sp_dc" cookie.')
            exit(1)
        token = json['accessToken']
        
        return token