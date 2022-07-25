# Comandi
Questa è una lista di comandi/istruzioni sul come preparare l'osservatorio per la sua funzione su debian e generalizzata il più possibile.
## Procedimento
Aggiungiamo la possibilità di creare ambienti virtuali per python. Su altre distro potrebbe non essere necessario/chiamarsi diversamente:
```
sudo apt-get install python3-venv
```
Installiamo unzip per scompattare gli zip. Su altre distro potrebbe non essere necessario
```
sudo apt-get install unzip
```
Creiamo l'ambiente virtuale e lo attiviamo
```
python3 -m venv .venv
```
```
source .venv/bin/activate
```
Installiamo le dipendenze richieste per eseguire gli script
```
pip install -r requirements.txt
```

Entriamo nella cartella dove posizioneremo i binari dei browser:
```
cd browserBin
```
Per gli utenti debian:
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
```
```
sudo apt install ./google-chrome-stable_current_amd64.deb
```
Se non sei utente debian dovrai installare chrome come più si confà alla tua distribuzione

Scarichiamo il binario di chrome e lo scompattiamo
```
curl -L https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1012728%2Fchrome-linux.zip\?generation\=1654813044687278\&alt\=media --output chrome-linux.zip
```
```
unzip chrome-linux.zip
```
Scarichiamo il binario di chromedriver e lo scompattiamo
```
curl -L https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1012728%2Fchromedriver_linux64.zip\?generation\=1654813050598651\&alt\=media --output chromedriver_linux64.zip
```
```
unzip chromedriver_linux64.zip
```
Usciamo dalla cartella
```
cd ..
```
Eseguiamo il download del dataset
```
python3 cli/data/enti/download.py
```
Normalizziamo il dataset, ricorda di aggiustare il comando così da usare la data odierna!
```
python3 cli/data/enti/normalize.py out/enti/2022-07-25/enti.tsv 
```
Avviamo il check. Ricorda anche qua di sistemare la data.
```
python3 cli/check/browsing.py out/enti/2022-07-25/dataset.tsv
```
