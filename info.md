# EGD Distribuce Power Data

** Testovací verze kompletně přepracovaného skriptu EGD **
**Použití na vlastní riziko**

Při reportování chyby, problému,... přikládejte log: /homeassistant/egddistribuce.log

## configuration.yaml

```yaml
sensor:
  - platform: egdczpowerdata
    client_id: xxxxxxxxxxxxxxxxxxxxxxx #Client ID z Portalu
    client_secret: yyyyyyyyyyyyyyyyyyyyyyy #client Secret z portalu
    ean: '000000EAN000000' #EAN Pokud máte Spotřební i výrobní EAN, zadejte spotřební, obsahuje oboje data
    days: 1 # Vzdy 1!!!
```

## Automatizace pro aktualizaci

Aktualizace se spouští pomocí události rund_egd, kterou lze buď vyvolat manuálně nebo pravidelně pomocí automatizace. Ideálně cca 0:30, maximálně však 4x za den (data se stejně u EGD neaktualizují častěji)

```yaml
alias: Run EGD
description: ""
trigger:
  - platform: time
    at: "00:30:00"
condition: []
action:
  - event: run_egd
mode: single
```

## Entity / Senzory

* sensor.egd_000000EAN000000_icc1 - entita s denni spotrebou z predchoziho dne
* sensor.egd_000000EAN000000_isc1 - entita s denni vyrobou z predchoziho dne


# Dlouhodobá statistika

Senzory standardně uchovávají data 10dní (v závislosti na nastavení retence vašeho HA). Následující konfigurace by měla zajistit (testuje se), že data sensor.egd_* zůstanou na trvalo. 

## configuration.yaml:

```yaml
recorder:
  purge_keep_days: 10  # Default HA retention
  include:
    entity_globs:
      - sensor.energy_*  # Include all energy sensors matching this pattern
      - sensor.egd_*
  exclude:
    domains:
      - sensor  # Exclude all sensors globally
    entity_globs:
      - sensor.energy_*  # Override exclusion to include energy sensors
      - sensor.egd_*
```
