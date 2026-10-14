# SL Departures för Home Assistant

Custom integration (HACS) som visar avgångstider för SL i Stockholm. Hållplats och filter ställs in i Home Assistants gränssnitt. Ingen API-nyckel behövs.

Data hämtas varje minut från SL:s öppna API (`transport.integration.sl.se`).

## Installation via HACS

1. Öppna HACS → Integrationer → menyn uppe till höger → **Anpassade databaser**.
2. Lägg till adressen till detta repo med kategori **Integration**.
3. Sök efter **SL Departures**, ladda ner och starta om Home Assistant.

### Manuell installation

Kopiera mappen `custom_components/sl_departures` till `config/custom_components/` och starta om Home Assistant.

## Konfiguration

1. Gå till **Inställningar → Enheter & tjänster → Lägg till integration** och välj **SL Departures**.
2. Skriv in hela eller delar av hållplatsens namn, t.ex. `Slussen`.
3. Välj hållplats i listan och ange vid behov:
   - **Trafikslag**: buss, tunnelbana, tåg, spårvagn, båt (tomt = alla)
   - **Max antal avgångar**
   - **Tidsfönster** i minuter
4. Upprepa för fler hållplatser. Inställningarna kan ändras senare via integrationens **Alternativ**.

## Sensor

Varje hållplats får sensorn `Next departure` (tidsstämpel för nästa avgång). Alla avgångar finns i attributet `departures`:

| Fält | Beskrivning |
| --- | --- |
| `line` | Linjenummer |
| `transport_mode` | Trafikslag |
| `destination` | Destination |
| `display` | Text som visas på skylt (t.ex. `3 min`) |
| `scheduled` / `expected` | Planerad / förväntad avgångstid |
| `state` | Avgångens status |
| `platform` | Läge/plattform |
| `deviations` | Avvikelsemeddelanden |

### Exempel: kort i Lovelace

```yaml
type: markdown
content: >
  {% for d in state_attr('sensor.slussen_next_departure', 'departures') %}
  **{{ d.line }}** {{ d.destination }} – {{ d.display }}
  {% endfor %}
```

Byt ut entitets-ID mot din egen sensor.

## Licens

Se [LICENSE](LICENSE).