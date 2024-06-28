# EGD Distribuce Power Data

**!!! po posledni aktualizaci HA se data zacala stahovat kazdou minutu a distribuce oslovuje uzivatele s nadmernym zatezovanim API. Prosim intergraci zatim nepouzivat, na aktualizaci se pracuje**

Integrace pro stahování dat o spotřebe a výrobě z EGD Distribuce.

Pokud se vám řešení líbí, můžete mne podpořit v další tvorbě a rozvoji - za což vám předem děkuji :)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ondrejv)

**Veřejné testování** 

**Použití na vlastní riziko**

Při reportování chyby, problému,... přikládejte log: /homeassistant/egddistribuce.log

## config.yaml

```yaml
sensor:
  - platform: egdczpowerdata
    client_id: xxxxxxxxxxxxxxxxxxxxxxx #Client ID z Portalu
    client_secret: yyyyyyyyyyyyyyyyyyyyyyy #client Secret z portalu
    ean: '000000EAN000000' #EAN Pokud máte Spotřební i výrobní EAN, zadejte spotřební, obsahuje oboje data
    days: 1 # Vzdy 1!!!
```

## Automatizace pro aktualizaci

Automatizace není potřeba, data se natahují průběžně automaticky, automatizací lze případně urychlit aktualizaci

```yaml
alias: Refresh EGD Power Data Sensor
action:
  - service: homeassistant.update_entity
    data: {}
    target:
      entity_id: sensor.egddistribuce_status_000000EAN000000_1 #Vyberte dle vaseho entitu EAN
```

## Entity

* sensor.egddistribuce_000000EAN000000_1_icc1 - entita s denni spotrebou z predchoziho dne
* sensor.egddistribuce_000000EAN000000_1_isc1 - entita s denni vyrobou z predchoziho dne
* sensor.egddistribuce_status_000000EAN000000_1 - Interni entita slouzici pro aktualizace

# Statisticke senzory

Nevim jak se to bude chovat v case a v pripadech, kdy se stazeni spusti vicekrat
