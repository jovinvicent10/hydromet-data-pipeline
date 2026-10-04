# HydroMet-ETL Data Dictionary

The interim file is `data/interim/nasa_power_tanzania_daily.csv`. The baseline grain is one location-date row from `NASA_POWER`. Dates follow the preserved payload's `LST` (local solar time) convention; daily labels are not UTC timestamps.

| Column | Logical type | Meaning and baseline unit |
|---|---|---|
| date | Date | `YYYY-MM-DD`, 2001-01-01 through 2025-12-31 |
| location | String | Configured point name; `Dar_es_Salaam` is the stored Dar es Salaam label |
| latitude | Number | Requested decimal degrees; south negative |
| longitude | Number | Requested decimal degrees; east positive |
| source | String | Pipeline provider identifier `NASA_POWER` |
| T2M | Number | Daily mean temperature at 2 m, °C |
| T2M_MIN | Number | Daily minimum temperature at 2 m, °C |
| T2M_MAX | Number | Daily maximum temperature at 2 m, °C |
| RH2M | Number | Relative humidity at 2 m, % |
| PRECTOTCORR | Number | Corrected daily precipitation, mm/day |
| WS2M | Number | Wind speed at 2 m, m/s |
| ALLSKY_SFC_SW_DWN | Number | All-sky surface shortwave downward radiation, **MJ/m²/day in the preserved baseline payload** |

All eight manifest-linked payloads were checked and report solar units MJ/m²/day and LST. The Arusha payload records API `v2.9.6`, fill value `-999.0`, time standard `LST` and the units above. The loader currently labels solar radiation `kWh/m2/day` without converting values. Interpret baseline values using the raw unit; resolve the discrepancy before energy calculations. A conversion from MJ to kWh would divide by 3.6 after confirming all source units. No code correction is made here.

Ordinary nulls and provider fill values are distinct. The quality evidence establishes zero ordinary missing values and compliance with implemented rules; it does not establish a dedicated sentinel-normalization policy for every variable.

Long-form `value` takes the unit of its joined variable, not a universal unit. The daily mart uses lowercase variable columns and `observation_date`, `location_name`, `source_name`. Monthly temperature, humidity, wind and radiation are arithmetic means; `total_precipitation` sums daily precipitation (mm over the month for daily intervals). `daily_observations` counts rows and does not alone establish completeness.

The ML target `target_precip_next_day` is next-row precipitation within location. Lags refer to earlier rows; rolling features average 7 or 30 prior rows after a one-row shift. Interpreting these as calendar days depends on continuous daily coverage. See [schema](database_schema.md), [lineage](data_lineage.md) and [datasheet](dataset_datasheet.md).
