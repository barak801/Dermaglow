import requests

def test_lunes(phone="573161154777"):
    url = "http://127.0.0.1:5000/webhook/"
    data = {"Body": "para lunes a las 3", "From": f"whatsapp:{phone}"}
    response = requests.post(url, data=data)
    return response.text

if __name__ == "__main__":
    print(test_lunes())
