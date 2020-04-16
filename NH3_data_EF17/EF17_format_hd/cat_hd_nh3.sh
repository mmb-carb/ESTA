path=../../output/emfac2017/v20200411/2024/hdv
for month in {01..12}; do
  export mth=$month

  for dd in {01..31} ; do
   export day=$dd
   if [ -d $path/$mth/$day ]
   then

   cat nh3_hd_2024.csv >> $path/$mth/$day/emfac_hd.csv_all

   fi
  done
done
