### Dock Plasma Cash Contracts  

#### NOTE:  
**Contracts are forked from [Loom Network](https://github.com/loomnetwork/plasma-cash). Please check each file in contracts for the applicable license.**  

**Contracts are beta and have not undergone a third-party review yet. Tread with care.**  


#### Prerequisites  
In order to use the enclosed python scripts, you need Python version >= 3.7.0 and web3py, py-solc, and requests and probably want docker. To install the python dependencies (ideally in a virtualenv):  

```bash
$ pip install -r requirements.txt
```  

#### Compiling the contracts  

Follow [Populous](https://populus.readthedocs.io/en/latest/deploy.html),  [Truffle](https://truffleframework.com/docs/truffle/getting-started/compiling-contracts), [py-solc](https://github.com/ethereum/py-solc), the [solidity](https://solidity.readthedocs.io/en/v0.4.24/installing-solidity.html) instructions to install and run solc. At this time, you want to stay < 0.5 and 0.4.24 is a good choice. From the command line:  

```bash
$ solc --version # should be 0.4.24
$ solc -o build --combined-json abi,bin --optimize  --optimize-runs=1 --evm-version byzantium contracts/*.sol
```  
Note that the evm-version default is _byzantium_ but with a fork afoot, you may want to keep this setting in mind.  

For a quick start, see the _compile\_to\_json.py_ script, which utilizes py-solc and assumes solc  0.4.24 is installed. If it is not, after ```$ pip install py-solc```, run ```$ python -m solc.install v0.4.24```. At least on OSX, the commandline installation, especially if another, newer version is already in place, seems to work reasonably well. If you have a higher version already installed with brew, for example, you may need to unlink.  

With a working solidity setup in place, you can either compile from the command line or utilize the _compile\_to\_json.py_ script. If you want to use the deployment scripts in _deploy.py_, you may want to utilize the script to keep changes to a minimum. 
``` $ python compile_to_json.py``` creates a _json_ dir and decomposes solc's _complete.json_ into individual *.json files including the abi and bin output, if applicable.  

#### Deploying the contracts  
**Contracts are beta and have not undergone a third-party review yet. Tread with care.**  

The _deploy.py_ script includes a fairly generic **deploy** function as well as a few support functions and a parameterized **quick_deploy** function. Note that if you want to work with the contracts post deployment, you want to persist the personal and contract accounts as well as the transaction receipts for future reference. Moreover, there are a few initialization parameters you may want to adjust depending on your use case. See _deploy.py_ for more details and definitely before running it.  

Note that **quick_deploy** assumes you have access to a running (dockerized) parity dev node. You don't have to have docker but it sure helps. Assuming you do:  

```bash 
$ docker pull parity/parity:stable	
```  

For a minimal parity dev client:  

```bash
$ docker run -d -ti \
                 -v ~/.parity/:/home/parity/.local/share/io.parity.ethereum/ \
                 -p 8545-8546:8545-8546 \
                 --name <your container name> parity/parity:v2.2.5 \
                 --chain dev \
                 --jsonrpc-interface all \
                 --jsonrpc-apis all \
                 --jsonrpc-cors all \
                 --jsonrpc-hosts all
```  

should do. Make sure you replace <_your container name_> with the actual name and adjust the local dir as needed. If you end up having trouble writing to the local volume ```chmod a+rwx -R <your dir>``` out to do the trick.  

With more scaffolding out of the way, it's time to deploy the contracts:  

```bash
$ python deploy.py
```  

is the anti-climactic last step.  

Finally, ff you like to keep an eye on things, open a separate terminal __before__ you deploy the contracts and:  

```bash 
$ docker logs -f <your_container_name or id>
``` 

You should see the block transactions corresponding to your deployment, e.g.:  

```bash 
2019-01-24 03:30:45 UTC    0/25 peers   433 KiB chain 3 MiB db 0 bytes queue 448 bytes sync  RPC:  0 conn,    0 req/s, 1460 µs
2019-01-24 03:30:47 UTC Imported #159 0x0984…81a4 (1 txs, 0.02 Mgas, 0 ms, 0.60 KiB) + another 7 block(s) containing 7 tx(s)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x0444d2f7a7c38168112af45e402a45c46f85bc1f68bc72f1bd372063a261a72f)
2019-01-24 03:30:47 UTC Transaction mined (hash 0xe7075a0aff0025975dc8266bb4b2bae483b2650780f42ebb4b1134b2742e1b3d)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x52a5085ad8cc8d3f5d617e718f2e3c0244c3ac8b634a36ef7cd8e1c8082f6a41)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x8f53bf2363d64c86c0e35596611fc0e7c0d0511b12633ae9350eb3f8a3fb2293)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x4f26797619365343997e7c407cac1e94198ec370d5caf5ae5da45e95a4b1f601)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x106951200faf1c3f6c6a4b00023c2779f7b4e12f516f213377ec9c511fc614f6)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x8e2412783edb5917392b55750f1384238c75729c96df245d402fb29807f8f3c9)
2019-01-24 03:30:47 UTC Transaction mined (hash 0x3fbdbe45cee3a48798db36c08bef9d155a8b513a2a7da75ffb223e82d6deebbb)
2019-01-24 03:31:15 UTC    0/25 peers   472 KiB chain 3 MiB db 0 bytes queue 448 bytes sync  RPC:  0 conn,    0 req/s, 1460 µs
```  








