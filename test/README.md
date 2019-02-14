#### Plasma Cash Tests  

**License [MIT](https://github.com/getdock/dock-plasma-cash/blob/contracts/LICENSE) unless otherwise specified.**

First cut.  

```bash
$ pytest -vv
```  
should do. We added compiled contract code in /json for convenience purposes but you should consider compiling from source against the most recent contract source.  

Right now, the tests are geared toward Parity Dev, see the [Readme](https://github.com/getdock/plasma-cash-contracts/tree/master/contracts) in contracts for more info.


To Do  
- [ ] finish type hints  
- [ ] finsih doc strings
- [ ] add smoker
- [ ] generalize eth client (beyond parity)
