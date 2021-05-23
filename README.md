# LAS-Randomizer
A randomizer for The Legend of Zelda: Link's Awakening remake. Currently still very early in development.

Currently you can generate randomizations by providing a logic, a seed, and one of a few options. There's no proper interface yet so there are still many options to implement and to present to the user. Currently,this only creates a spoiler log, not a playable game modification.

### How to run:

`python main.py <seed> <logic> <other settings, space separated>`

Seed can be any string.

Valid logics are `basic`, `advanced`, `glitched`, and `none`. Note that the advanced and glitched logics aren't fully developed yet.

Valid extra options currently are:
```
fast-trendy : removes all instrument requirements from obtaining the trendy game prizes.
free-fishing : removes all instrument requirements for types of fish to appear in the pond.
free-shop : removes intrument/dungeon conditions for buying items from the shop.
free-book : the magnifying lens is not required to read the book which reveals the egg path.
```

All options can be ommitted, in which case seed is determined using system time, and logic is assumed to be `basic`.