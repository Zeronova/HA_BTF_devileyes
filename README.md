# BTF Lighting Devil Eyes

Home Assistant Integration für das 590×120mm Flexible RGB LED Matrix Panel „Devil Eyes" (Jieli AC695X) von BTF Lighting via Bluetooth.

An/Aus, Helligkeit und Flip-Modus – direkt über Home Assistant.

## Installation

### HACS (empfohlen)

1. HACS → Custom Repositories → Repository hinzufügen
2. URL: `https://github.com/Zeronova/HA_BTF_devileyes`
3. Kategorie: Integration
4. HACS → Integrationen → BTF Lighting Devil Eyes installieren
5. Home Assistant neustarten

### Manuell

1. Ordner `custom_components/btf_devileyes/` in den HA `config`-Ordner kopieren
2. Home Assistant neustarten

## Konfiguration

Einstellungen → Geräte & Dienste → Integration hinzufügen → **BTF Lighting Devil Eyes**

1. Bluetooth-Gerät scan (oder MAC-Adresse eingeben)
2. Das Panel sollte als `BTF-LIGHTING` (oder `ckc_...`) sichtbar sein
3. Verbinden → Fertig

Das Panel erscheint als:
- **Light** – Ein/Aus, Helligkeit
- **Select** – Flip-Modus (None / XY / X / Y)

## Supported devices

- 590×120mm Flexible RGB LED Matrix Panel „Devil Eyes" (BTF Lighting)
- Jieli AC695X Chip
- BLE Service 0xFFF0, Characteristic 0xFFF1
