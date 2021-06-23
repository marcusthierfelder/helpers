Test um EU Zertifikate zu erzeugen

# das ganze braucht python3 und ein TI-Konnektor und eine Route zu dem für die Server:


# für PU
sudo route -n add 100.102.0.0/17 KON-IP
sudo route -n add 100.103.0.0/16 KON-IP
sudo route -n add 100.102.128.0/17 KON-IP
# für RU
sudo route -n add 10.30.17.10/24 KON-IP


# anpassen der daten im request.py relativ weit oben


pip3 install -r requirements.txt

python3 request.py

