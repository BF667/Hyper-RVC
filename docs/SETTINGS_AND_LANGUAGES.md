# Hyper-RVC Settings & Languages

## Overview
This document describes the settings system and multi-language support in Hyper-RVC. The application supports **135 languages** with automatic locale detection and community-contributed translations.

## Supported Languages

### Language Files Location
`assets/i18n/languages/`

### Full Language List (135 Languages)

#### Major Languages (Full Translation)
| Code | Language | Region |
|------|----------|--------|
| en_US | English | US |
| en_GB | English | UK |
| en_AU | English | Australia |
| en_CA | English | Canada |
| en_IN | English | India |
| zh_CN | Chinese (Simplified) | China |
| zh_TW | Chinese (Traditional) | Taiwan |
| zh_HK | Chinese (Traditional) | Hong Kong |
| ja_JP | Japanese | Japan |
| ko_KR | Korean | Korea |
| es_ES | Spanish | Spain |
| es_MX | Spanish | Mexico |
| es_AR | Spanish | Argentina |
| es_CO | Spanish | Colombia |
| fr_FR | French | France |
| fr_CA | French | Canada |
| fr_BE | French | Belgium |
| de_DE | German | Germany |
| de_AT | German | Austria |
| de_CH | German | Switzerland |
| it_IT | Italian | Italy |
| it_CH | Italian | Switzerland |
| pt_BR | Portuguese | Brazil |
| pt_PT | Portuguese | Portugal |
| ru_RU | Russian | Russia |
| ru_KZ | Russian | Kazakhstan |
| ar_SA | Arabic | Saudi Arabia |
| ar_EG | Arabic | Egypt |
| ar_MA | Arabic | Morocco |
| hi_IN | Hindi | India |
| tr_TR | Turkish | Turkey |
| pl_PL | Polish | Poland |
| nl_NL | Dutch | Netherlands |
| nl_BE | Dutch | Belgium |
| sv_SE | Swedish | Sweden |
| sv_FI | Swedish | Finland |
| cs_CZ | Czech | Czech Republic |
| ro_RO | Romanian | Romania |
| id_ID | Indonesian | Indonesia |
| vi_VN | Vietnamese | Vietnam |
| th_TH | Thai | Thailand |
| uk_UA | Ukrainian | Ukraine |

#### European Languages
| Code | Language | Region |
|------|----------|--------|
| da_DK | Danish | Denmark |
| fi_FI | Finnish | Finland |
| el_GR | Greek | Greece |
| he_IL | Hebrew | Israel |
| hu_HU | Hungarian | Hungary |
| no_NO | Norwegian | Norway |
| nn_NO | Norwegian Nynorsk | Norway |
| sk_SK | Slovak | Slovakia |
| ca_ES | Catalan | Spain |
| eu_ES | Basque | Spain |
| gl_ES | Galician | Spain |
| is_IS | Icelandic | Iceland |
| sq_AL | Albanian | Albania |
| be_BY | Belarusian | Belarus |
| bs_BA | Bosnian | Bosnia |
| cy_GB | Welsh | UK |
| fo_FO | Faroese | Faroe Islands |
| ga_IE | Irish | Ireland |
| gd_GB | Scottish Gaelic | UK |
| lb_LU | Luxembourgish | Luxembourg |
| oc_FR | Occitan | France |
| sc_IT | Sardinian | Italy |
| et_EE | Estonian | Estonia |
| lv_LV | Latvian | Latvia |
| lt_LT | Lithuanian | Lithuania |
| sl_SI | Slovenian | Slovenia |
| sr_RS | Serbian | Serbia |
| hr_HR | Croatian | Croatia |
| bg_BG | Bulgarian | Bulgaria |
| fil_PH | Filipino | Philippines |

#### Asian Languages
| Code | Language | Region |
|------|----------|--------|
| am_ET | Amharic | Ethiopia |
| as_IN | Assamese | India |
| az_AZ | Azerbaijani | Azerbaijan |
| bo_CN | Tibetan | China |
| br_FR | Breton | France |
| ha_NG | Hausa | Nigeria |
| haw_US | Hawaiian | US |
| hy_AM | Armenian | Armenia |
| ig_NG | Igbo | Nigeria |
| ka_GE | Georgian | Georgia |
| kk_KZ | Kazakh | Kazakhstan |
| km_KH | Khmer | Cambodia |
| ku_TR | Kurdish | Turkey |
| ky_KG | Kyrgyz | Kyrgyzstan |
| lg_UG | Luganda | Uganda |
| ln_CD | Lingala | DR Congo |
| lo_LA | Lao | Laos |
| mg_MG | Malagasy | Madagascar |
| mi_NZ | Maori | New Zealand |
| mk_MK | Macedonian | North Macedonia |
| mn_MN | Mongolian | Mongolia |
| mt_MT | Maltese | Malta |
| my_MM | Burmese | Myanmar |
| ne_NP | Nepali | Nepal |
| or_IN | Odia | India |
| pa_IN | Punjabi | India |
| pa_PK | Punjabi | Pakistan |
| ps_AF | Pashto | Afghanistan |
| sd_PK | Sindhi | Pakistan |
| si_LK | Sinhala | Sri Lanka |
| su_ID | Sundanese | Indonesia |
| tg_TJ | Tajik | Tajikistan |
| tk_TM | Turkmen | Turkmenistan |
| tl_PH | Tagalog | Philippines |
| tt_RU | Tatar | Russia |
| ug_CN | Uyghur | China |
| uz_UZ | Uzbek | Uzbekistan |
| ms_MY | Malay | Malaysia |
| ms_SG | Malay | Singapore |
| sw_KE | Swahili | Kenya |
| sw_TZ | Swahili | Tanzania |

#### Indian Languages
| Code | Language | Region |
|------|----------|--------|
| bn_BD | Bengali | Bangladesh |
| ta_IN | Tamil | India |
| te_IN | Telugu | India |
| ml_IN | Malayalam | India |
| mr_IN | Marathi | India |
| gu_IN | Gujarati | India |
| kn_IN | Kannada | India |
| fa_IR | Persian (Farsi) | Iran |
| ur_PK | Urdu | Pakistan |

#### African & Indigenous Languages
| Code | Language | Region |
|------|----------|--------|
| af_ZA | Afrikaans | South Africa |
| bm_ML | Bambara | Mali |
| ee_GH | Ewe | Ghana |
| qu_PE | Quechua | Peru |
| rn_BI | Rundi | Burundi |
| rw_RW | Kinyarwanda | Rwanda |
| sa_IN | Sanskrit | India |
| so_SO | Somali | Somalia |
| wo_SN | Wolof | Senegal |
| xh_ZA | Xhosa | South Africa |
| yi_US | Yiddish | US |
| yo_NG | Yoruba | Nigeria |
| zu_ZA | Zulu | South Africa |

## Adding a New Language
1. Create a new JSON file in `assets/i18n/languages/`
2. Name it using the format: `{language_code}_{country_code}.json`
3. Copy all keys from `en_US.json` as the base
4. Translate the values to your target language
5. Add a display name entry to the `language_names` dict in `tabs/settings.py`
6. The language will automatically appear in the settings dropdown

Example structure:
```json
{
    "Appearance": "Your Translation",
    "Theme": "Your Translation",
    "Language": "Your Translation",
    ...
}
```

## Configuration
Language settings are stored in `assets/config.json`:
```json
{
  "lang": {
    "override": false,
    "selected_lang": "en_US"
  }
}
```

## i18n Module Usage
```python
from assets.i18n.i18n import I18nAuto

i18n = I18nAuto()
text = i18n("Theme")  # Returns translated text
current = i18n.get_current_language()
i18n.reload_language("es_ES")  # Switch language
```

## Translation Coverage
- **Full translation** (~185 keys): Major languages with complete coverage
- **Core translation** (~60-65 keys): Newer languages with essential UI strings translated
- **English fallback**: Remaining keys show English text (graceful fallback)

The system automatically falls back to the English key if a translation is not found, ensuring the UI remains functional in all languages.
