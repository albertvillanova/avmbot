# avmbot

Wikidata bot


## TODO

- cantons before/after 2015 should be different items?
  - Q66364085 is *canton of Denain* AFTER 2015 (in DE Wikipedia)

- canton of Avesnes-le-Comte
  - no ca description and ca label starts with capital *Cantó*
  - in 2015 it changed:
    - surface: 177 -> 643
    - number of municipalities: 31 -> 108
  - fix ALL cantons

- DONE: Fix bug: use 2017 COG instead of current
  - Now population is wrongly added to new communes created after 2017 (with INSEE code equal to the one of a previous commune), while population is not added to the previous commune
  
- Administrative divisions without INSEE code
  - DONE: arrondissements
  - TODO: cantons
    - canton of France (until 2015)
    - canton of France (starting March 2015)
  - DONE: communes associées ou déléguées
    - see add population log file: either unknown or wrong INSEE code
    - DONE

- DONE New population quantity equal to previous population
  - What to do? New statement? New qualifier?
    - New statement
  
- Add contains administrative territorial entity [P150]
 
 
- DONE Communes: Ogy, Lendou-en-Quercy, Sermentot

-  Le Massegros (Q721291) 

- Other populations
 
 
## Items and properties

- Former:

  - instance of [P31]
  
    - end time [P582]
    
  - dissolved, abolished or demolished [P576]
  
  - replaced by [P1366]
  
  - INSEE code
  
    - end time
    
- New:

  - instance of [P31]
  
    - start time [P580]
    
  - inception [P571]
  
  - replaces [P1365]
  
  - INSEE code
  
    - start time [P580]
