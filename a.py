from requests import get, head

## stream


# get file size
def get_file_size(url: str) -> int:
    return int(head(url).headers["Content-Length"])


# download file
def download_file_as_stream(url: str, filename: str) -> None:
    with open(filename, "wb") as f:
        for chunk in get(url, stream=True).iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


download_file_as_stream(
    "https://media.fastdl.app/get?__sig=u4t790FeLK-hy5-ZUUIqFQ&__expires=1716716001&uri=https%3A%2F%2Finstagram.faca1-1.fna.fbcdn.net%2Fv%2Ft66.30100-16%2F318160593_439713225338211_640522898023928141_n.mp4%3F_nc_ht%3Dinstagram.faca1-1.fna.fbcdn.net%26_nc_cat%3D103%26_nc_ohc%3DBQcA6Zt4RQEQ7kNvgEMtRDv%26edm%3DAP_V10EBAAAA%26ccb%3D7-5%26oh%3D00_AYAcbzksmbwslJG0zhiWv6BMhARXRzOsHGBNrRFwmBEIPg%26oe%3D66543340%26_nc_sid%3D2999b8%26dl%3D1&filename=%E0%B4%92%E0%B4%B0%E0%B5%81%20%E0%B4%95%E0%B4%BE%E0%B4%B2%E0%B4%A4%E0%B5%8D%E0%B4%A4%E0%B5%8D%20%E0%B4%A4%E0%B4%B0%E0%B4%82%E0%B4%97%E0%B4%82%20%E0%B4%B8%E0%B5%83%E0%B4%B7%E0%B5%8D%E2%80%8C%E0%B4%9F%E0%B4%BF%E0%B4%9A%E0%B5%8D%E0%B4%9A%20%E0%B4%AA%E0%B4%BE%E0%B4%9F%E0%B5%8D%E0%B4%9F%E0%B5%8D%20%20%EF%B8%8F%20.......mp4&ua=-&referer=https%3A%2F%2Fwww.instagram.com%2F",
    "new.mp4",
)
