```
pip install nrgise
```
**Note that it is recommended to pin the version of the nrgise (e.g. `nrgise==0.X.Y`) to be safe from breaking changes of future versions**

Some of the controllers used in nrgise require a solver. You can install a solver e.g. by:
```
conda install conda-forge/label/cf202003::ipopt -y --override-channels -c conda-forge
```