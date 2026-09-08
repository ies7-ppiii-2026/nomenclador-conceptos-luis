# Datos Crudos - Experimentos

## Origen de los archivos

- **ICD-10**: https://icdcdn.who.int/icd10/claml/icd102019en.xml.zip
- **ICD-11**: https://icdcdn.who.int/static/releasefiles/2026-01/SimpleTabulation-ICD-11-MMS-en.zip
- **Mapping**: https://icdcdn.who.int/static/releasefiles/2026-01/mapping.zip

## SHA-256 Hashes

| Archivo | Hash |
|---------|------|
| `icd10/icd102019en.xml.zip` | `344c571aa9aed3b9ad1c80261b7828c45cfb5fc0b1a5da64aecef354dff5b3d9` |
| `icd11/SimpleTabulation-ICD-11-MMS-en.zip` | `f1356588f40953a83e3af2b662deab47c5e269f944d1ea4ed0cfeb2007c7cd39` |
| `mapping/mapping.zip` | `2eb158cf2a0d53690d6e9baf0956f7617e1315e4f2a44dfc3db3be8f49193a1d` |

## Notas

- **`mapping/`** contiene el ground truth oficial para evaluación. No debe ser modificado.
- Los datos pesados (ZIPs y archivos extraídos) no se incluyen en el PR.
- Estructura verificada: coincide exactamente con la especificación del issue #1.
