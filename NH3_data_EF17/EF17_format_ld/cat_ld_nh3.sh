path=../../output/emfac2017/v20200411/2024/ldv
for month in {01..12}; do
  export mth=$month

  for dd in {01..31} ; do
   export day=$dd
   if [ -d $path/$mth/$day ]
   then

   grep 'Alameda (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Alameda_SF_BA_emission.csv
   grep 'Alpine (GBV)' nh3_ld_2024.csv >> $path/$mth/$day/Alpine_GBV_GBU_emission.csv
   grep 'Amador (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Amador_MC_AMA_emission.csv
   grep 'Butte (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Butte_SV_BUT_emission.csv
   grep 'Calaveras (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Calaveras_MC_CAL_emission.csv
   grep 'Colusa (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Colusa_SV_COL_emission.csv
   grep 'Contra Costa (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Contra_Costa_SF_BA_emission.csv
   grep 'Del Norte (NC)' nh3_ld_2024.csv >> $path/$mth/$day/Del_Norte_NC_NCU_emission.csv
   grep 'El Dorado (LT)' nh3_ld_2024.csv >> $path/$mth/$day/El_Dorado_LT_ED_emission.csv
   grep 'El Dorado (MC)' nh3_ld_2024.csv >> $path/$mth/$day/El_Dorado_MC_ED_emission.csv
   grep 'Fresno (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Fresno_SJV_SJU_emission.csv
   grep 'Glenn (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Glenn_SV_GLE_emission.csv
   grep 'Humboldt (NC)' nh3_ld_2024.csv >> $path/$mth/$day/Humboldt_NC_NCU_emission.csv
   grep 'Imperial (SS)' nh3_ld_2024.csv >> $path/$mth/$day/Imperial_SS_IMP_emission.csv
   grep 'Inyo (GBV)' nh3_ld_2024.csv >> $path/$mth/$day/Inyo_GBV_GBU_emission.csv
   grep 'Kern (MD)' nh3_ld_2024.csv >> $path/$mth/$day/Kern_MD_KER_emission.csv
   grep 'Kern (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Kern_SJV_SJU_emission.csv
   grep 'Kings (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Kings_SJV_SJU_emission.csv
   grep 'Lake (LC)' nh3_ld_2024.csv >> $path/$mth/$day/Lake_LC_LAK_emission.csv
   grep 'Lassen (NEP)' nh3_ld_2024.csv >> $path/$mth/$day/Lassen_NEP_LAS_emission.csv
   grep 'Los Angeles (MD)' nh3_ld_2024.csv >> $path/$mth/$day/Los_Angeles_MD_AV_emission.csv
   grep 'Los Angeles (SC)' nh3_ld_2024.csv >> $path/$mth/$day/Los_Angeles_SC_SC_emission.csv
   grep 'Madera (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Madera_SJV_SJU_emission.csv
   grep 'Marin (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Marin_SF_BA_emission.csv
   grep 'Mariposa (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Mariposa_MC_MPA_emission.csv
   grep 'Mendocino (NC)' nh3_ld_2024.csv >> $path/$mth/$day/Mendocino_NC_MEN_emission.csv
   grep 'Merced (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Merced_SJV_SJU_emission.csv
   grep 'Modoc (NEP)' nh3_ld_2024.csv >> $path/$mth/$day/Modoc_NEP_MOD_emission.csv
   grep 'Mono (GBV)' nh3_ld_2024.csv >> $path/$mth/$day/Mono_GBV_GBU_emission.csv
   grep 'Monterey (NCC)' nh3_ld_2024.csv >> $path/$mth/$day/Monterey_NCC_MBU_emission.csv
   grep 'Napa (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Napa_SF_BA_emission.csv
   grep 'Nevada (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Nevada_MC_NSI_emission.csv
   grep 'Orange (SC)' nh3_ld_2024.csv >> $path/$mth/$day/Orange_SC_SC_emission.csv
   grep 'Placer (LT)' nh3_ld_2024.csv >> $path/$mth/$day/Placer_LT_PLA_emission.csv
   grep 'Placer (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Placer_MC_PLA_emission.csv
   grep 'Placer (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Placer_SV_PLA_emission.csv
   grep 'Plumas (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Plumas_MC_NSI_emission.csv
   grep 'Riverside (MD/MDAQMD)' nh3_ld_2024.csv >> $path/$mth/$day/Riverside_MD_MOJ_emission.csv
   grep 'Riverside (MD/SCAQMD)' nh3_ld_2024.csv >> $path/$mth/$day/Riverside_MD_SC_emission.csv
   grep 'Riverside (SC)' nh3_ld_2024.csv >> $path/$mth/$day/Riverside_SC_SC_emission.csv
   grep 'Riverside (SS)' nh3_ld_2024.csv >> $path/$mth/$day/Riverside_SS_SC_emission.csv
   grep 'Sacramento (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Sacramento_SV_SAC_emission.csv
   grep 'San Benito (NCC)' nh3_ld_2024.csv >> $path/$mth/$day/San_Benito_NCC_MBU_emission.csv
   grep 'San Bernardino (MD)' nh3_ld_2024.csv >> $path/$mth/$day/San_Bernardino_MD_MOJ_emission.csv
   grep 'San Bernardino (SC)' nh3_ld_2024.csv >> $path/$mth/$day/San_Bernardino_SC_SC_emission.csv
   grep 'San Diego (SD)' nh3_ld_2024.csv >> $path/$mth/$day/San_Diego_SD_SD_emission.csv
   grep 'San Francisco (SF)' nh3_ld_2024.csv >> $path/$mth/$day/San_Francisco_SF_BA_emission.csv
   grep 'San Joaquin (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/San_Joaquin_SJV_SJU_emission.csv
   grep 'San Luis Obispo (SCC)' nh3_ld_2024.csv >> $path/$mth/$day/San_Luis_Obispo_SCC_SLO_emission.csv
   grep 'San Mateo (SF)' nh3_ld_2024.csv >> $path/$mth/$day/San_Mateo_SF_BA_emission.csv
   grep 'Santa Barbara (SCC)' nh3_ld_2024.csv >> $path/$mth/$day/Santa_Barbara_SCC_SB_emission.csv
   grep 'Santa Clara (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Santa_Clara_SF_BA_emission.csv
   grep 'Santa Cruz (NCC)' nh3_ld_2024.csv >> $path/$mth/$day/Santa_Cruz_NCC_MBU_emission.csv
   grep 'Shasta (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Shasta_SV_SHA_emission.csv
   grep 'Sierra (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Sierra_MC_NSI_emission.csv
   grep 'Siskiyou (NEP)' nh3_ld_2024.csv >> $path/$mth/$day/Siskiyou_NEP_SIS_emission.csv
   grep 'Solano (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Solano_SF_BA_emission.csv
   grep 'Solano (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Solano_SV_YS_emission.csv
   grep 'Sonoma (NC)' nh3_ld_2024.csv >> $path/$mth/$day/Sonoma_NC_NS_emission.csv
   grep 'Sonoma (SF)' nh3_ld_2024.csv >> $path/$mth/$day/Sonoma_SF_BA_emission.csv
   grep 'Stanislaus (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Stanislaus_SJV_SJU_emission.csv
   grep 'Sutter (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Sutter_SV_FR_emission.csv
   grep 'Tehama (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Tehama_SV_TEH_emission.csv
   grep 'Trinity (NC)' nh3_ld_2024.csv >> $path/$mth/$day/Trinity_NC_NCU_emission.csv
   grep 'Tulare (SJV)' nh3_ld_2024.csv >> $path/$mth/$day/Tulare_SJV_SJU_emission.csv
   grep 'Tuolumne (MC)' nh3_ld_2024.csv >> $path/$mth/$day/Tuolumne_MC_TUO_emission.csv
   grep 'Ventura (SCC)' nh3_ld_2024.csv >> $path/$mth/$day/Ventura_SCC_VEN_emission.csv
   grep 'Yolo (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Yolo_SV_YS_emission.csv
   grep 'Yuba (SV)' nh3_ld_2024.csv >> $path/$mth/$day/Yuba_SV_FR_emission.csv

   fi
  done
done
