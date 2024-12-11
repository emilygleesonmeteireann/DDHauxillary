# DDH in HARMONIE-AROME

Diagnostics on a horizontal domain (DDH) was originally developed in Météo-France as a tool to provide, on user-defined domains, 
the budget of prognostic variables of NWP models (momentum, temperature, water vapour, etc). The DDH tool is used by researchers 
and model developers to understand the model’s dynamical and physical interactions and tendencies, thus contributing to the 
parametrization development process. Each model point is described within the DDH software by its geographical position, 
a scale factor, the orientation of the geographical North vector, a mean value of each variable as well as some horizontal 
derivatives.

# Running an experiment with DDH (on ATOS)

1) You can use the main cy46 repo as the changes are there now.

```bash
mkdir -p $SCRATCH/harmonie_releases/git/HCY46_DDH
cd $SCRATCH/harmonie_releases/git/HCY46_DDH
git clone git@github.com:Hirlam/Harmonie.git
cd Harmonie
```
2) Set-up a HARMONIE experiment as normal. Update your config_exp.h

- To use DDH, set USEDDH="yes" in ecf/config_exp.h
- To archive DDH data to ec or ectmp include ddh in the archiving strategy in ecf/config_exp.h

```bash
ARSTRATEGY="climate:fg:verif:odb_stuff: \
              [an|fc]_fa:pp_gr: \
              _nc:_json:ddh"                  # Files to archive on ECFS, see above for syntax
```

- Set TFLAG to minute (min) if you wish to have minute output (hourly output is OK too). Note that the conversion of FA to grib format does not automatically work with this setting so it is best to set the conversion to "no".

If TFLAG="min", you need to change the file output times to something like
```bash
  HWRITUPTIMES="00-4320:60"               # History file output times
  FULLFAFTIMES=$HWRITUPTIMES              # History FA file IO server gather times
  PWRITUPTIMES="00-4320:15"               # Postprocessing times
  VERITIMES="00-4320:60"                  # Verification output times, may change PWRITUPTIMES
  SFXSELTIMES=$HWRITUPTIMES               # Surfex select file output times
  SFXSWFTIMES=-1                          # SURFEX select FA file IO server gathering times
  SWRITUPTIMES="00-180:60"                      # Surfex model state output times
  SFXWFTIMES=$SWRITUPTIMES                # SURFEX history FA file IO server gathering times
```
