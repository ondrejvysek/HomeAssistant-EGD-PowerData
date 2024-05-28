# EGD Distribuce Power Data

Integrace pro stahování dat o spotřebe a výrobě z EGD Distribuce.

Pokud se vám řešení líbí, můžete mne podpořit v další tvorbě a rozvoji - za což vám předem děkuji :)

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/ondrejv)

**Probíhá intenzivní vývoj a testování** 

**Použití na vlastní riziko**

## config.yaml

```yaml
sensor:
  - platform: egdpowerdata
    client_id: xxxxxxxxxxxxxxxxxxxxxxx #Client ID z Portalu
    client_secret: yyyyyyyyyyyyyyyyyyyyyyy #client Secret z portalu
    ean: '000000EAN000000' #EAN
    days: 1 # Vzdy 1!!!
```

## Automatizace pro aktualizaci

```yaml
alias: Refresh EGD Power Data Sensor
trigger:
  - platform: time
    at: "00:35:00"
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
