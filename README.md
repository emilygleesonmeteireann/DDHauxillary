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
