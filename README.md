# bicerin
Working on the RV challenge in Torino


## Milestones

The goal of this project is to analyse the RV challenge data.  
Right now the repository has a template implementation of the RJ-DNest code, which includes a quasi-periodic GP to model the stellar activity RV signal. Ideally this can be easily applied to the RV challenge data, but some practicalities have to be taken into account, mainly linear trends and the fact that each data set has around 500 points. 

- [x] implement a linear trend  
      went ahead and added a quadratic trend. So far so good but I'm not sure about the interaction with the GP
- [ ] implement HODLR inversion (issue [#1](https://github.com/j-faria/bicerin/issues/1))  
      issue is closed
- [x] implement celerite


All data is in the `data` folder and some metadata is in the `docs` and `reports` folders. 

### submodule update

On Apr 22 I decided to include `DNest4`, `eigen` and `celerite` as submodules within the bicerin tree.
Hopefully this makes it easier and faster to get this project set up and running.



## To run

- Compile with `make`
- Change `OPTIONS`
- Run `./main` or `./run`
- Analyse with `scripts/showresults.py` and `scripts/display.py`


[![Documentation](https://readthedocs.org/projects/bicerin/badge/?version=latest)](http://bicerin.readthedocs.io/?badge=latest)
