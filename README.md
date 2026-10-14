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
   - **Destination**: visar bara avgångar vars destination innehåller texten, t.ex. `Odenplan` eller `Odenplan, Kungsträdgården` (tomt = alla)
   - **Slutstation för resa**: ange en valfri slutstation (t.ex. `Slussen`) för att få resor från vald hållplats dit, även om det inte är linjens ändstation. Sensorn visar då avgång, antal byten och total restid (tomt = vanliga avgångar)
   - **Max antal avgångar**
   - **Tidsfönster** i minuter
4. Upprepa för fler hållplatser. Samma hållplats kan läggas till flera gånger med olika **Slutstation för resa**; varje post får egna sensorer och heter t.ex. `Mensättra → Slussen`.

### Ändra hållplats eller filter

Öppna integrationen och välj **Alternativ**. Skriv ett nytt hållplatsnamn för att byta hållplats, eller lämna fältet tomt för att behålla nuvarande. Därefter kan du ändra trafikslag, destination, antal avgångar och tidsfönster. Sensorn behåller sitt entitets-ID.

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

### Resor med slutstation

Om **Slutstation för resa** är ifylld får hållplatsen även sensorerna `Interchanges` (antal byten) och `Travel time` (total restid i minuter) för den första resan. Attributet `departures` innehåller då för varje resa: `line`, `transport_mode`, `scheduled`, `expected`, `arrival`, `destination` (slutstation), `interchange_stops` (stationer där du byter), `platform`, `interchanges`, `duration_minutes` och `legs` (delsträckor med `line`, `from`, `to`).

## Licens

Se [LICENSE](LICENSE).

---

# SL Departures for Home Assistant

Custom integration (HACS) that shows departure times for SL in Stockholm. The stop and filters are set in the Home Assistant UI. No API key is needed.

Data is fetched every minute from SL's open API (`transport.integration.sl.se`).

## Installation via HACS

1. Open HACS → Integrations → menu in the top right → **Custom repositories**.
2. Add the URL of this repo with category **Integration**.
3. Search for **SL Departures**, download it and restart Home Assistant.

### Manual installation

Copy the folder `custom_components/sl_departures` to `config/custom_components/` and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration** and choose **SL Departures**.
2. Enter all or part of the stop name, e.g. `Slussen`.
3. Pick the stop from the list and optionally set:
   - **Transport modes**: bus, metro, train, tram, ship (empty = all)
   - **Destination**: only shows departures whose destination contains the text, e.g. `Odenplan` or `Odenplan, Kungsträdgården` (empty = all)
   - **Journey end stop**: enter any stop (e.g. `Slussen`) to get journeys from the selected stop to it, even if it is not the line's terminus. The sensor then shows departure, number of changes and total travel time (empty = regular departures)
   - **Max departures**
   - **Time window** in minutes
4. Repeat for more stops. The same stop can be added several times with different **Journey end stop** values; each entry gets its own sensors and is named e.g. `Mensättra → Slussen`.

### Change stop or filters

Open the integration and choose **Configure**. Enter a new stop name to change stop, or leave the field empty to keep the current one. You can then change transport modes, destination, number of departures and time window. The sensor keeps its entity ID.

## Sensor

Each stop gets a `Next departure` sensor (timestamp of the next departure). All departures are available in the `departures` attribute:

| Field | Description |
| --- | --- |
| `line` | Line number |
| `transport_mode` | Transport mode |
| `destination` | Destination |
| `display` | Text shown on the sign (e.g. `3 min`) |
| `scheduled` / `expected` | Scheduled / expected departure time |
| `state` | Departure status |
| `platform` | Platform |
| `deviations` | Deviation messages |

### Example: Lovelace card

```yaml
type: markdown
content: >
  {% for d in state_attr('sensor.slussen_next_departure', 'departures') %}
  **{{ d.line }}** {{ d.destination }} – {{ d.display }}
  {% endfor %}
```

Replace the entity ID with your own sensor.

### Journeys with an end stop

If **Journey end stop** is set, the stop also gets the sensors `Interchanges` (number of changes) and `Travel time` (total travel time in minutes) for the first journey. The `departures` attribute then contains, for each journey: `line`, `transport_mode`, `scheduled`, `expected`, `arrival`, `destination` (end stop), `interchange_stops` (stops where you change), `platform`, `interchanges`, `duration_minutes` and `legs` (parts with `line`, `from`, `to`).

## License

See [LICENSE](LICENSE).