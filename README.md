# cloud-computing-project

This README contains reproducibility instructions for our project for EN.601.419, Cloud Computing.

## Summary
* Reproducing Figure 9
* Finding average path length before and after link failure
* Finding network connectivity before and after link failure
* Running Jellyfish topology in Mininet
* Authors
* Acknowledgement 
  
### Reproducing Fig. 9

1. In count_paths.py, set n as the desired number of switches and d to the number of inter-switch links in the main function.
2. Run file count_paths.py, with the command:
    `python count_paths.py`
3. The reproduced figure 9 can then be found in `figure_9_d_{d value}_n_{n value}.png` in the plots folder.

### Finding average path length before and after link failure
1. In count_paths.py, set n as the desired number of switches and d to the number of inter-switch links in the main function.
2. Set failProb as the probability of failure for each link.
3. Run file count_paths.py, with the command:
    `python count_paths.py`
3. The average path length can then be found in `avgPathLen_failProb_{fail prob value}_d_{d value}_n_{n value}.png` in the plots/path lengths folder.

### Finding network connectivity before and after link failure
1. In count_paths.py, set n as the desired number of switches and d to the number of inter-switch links in the main function.
2. Set failProb as the probability of failure for each link.
3. Run file count_paths.py, with the command:
    `python count_paths.py`
3. The connectivity will be printed on Terminal, but can also be found in `failProb_{fail prob value}_d_{d value}_n_{n value}.txt` in the connectivity lengths folder.

### Running Jellyfish in Mininet

#### Setup
1. First, we need to install Mininet. You can follow Option 1 listed in the instructions here: http://mininet.org/download/
2. Open VirtualBox.
3. Select "Mininet-VM" and click on "Start".
4. Login to Mininet with the username: mininet and password: mininet
5. Make sure eth0 is up:
   - run the command: `ifconfig eth0`
   - check the `inet addr` field. If it does not have an IP address, then run the command: `sudo dhclient eth0` and repeat step (a).
6. POX should be pre-installed. Please check the home folder and see if there is a folder called "pox". If not, please do: `git clone https://github.com/noxrepo/pox`
7. Install a GUI in the VM
   - Install the GUI:  
    `sudo apt-get update`  
    `sudo apt-get install openbox xinit -y`
   - If the above command doesn't work, please try: `sudo apt-get install xinit` and try again
   - Start the GUI  
     `startx`

#### Running the Jellyfish topology
1. Create a new terminal by right-clicking on the VM desktop and selecting "Terminal emulator"
2. Clone this repo (or just `mn_jellyfish_topology.py`) into the home folder
3. Ensure networkx is installed: `pip install networkx`
4. In a separate terminal, start the POX controller with the command:  
   `./pox/pox.py forwarding.l2_learning`
5. In the original terminal, run `python mn_jellyfish_topology.py` (or `python ./cloud-computing-project/mn_jellyfish_topology.py` if you cloned the entire repo)
   - Wait until the terminal changes to look like: `mininet>`
6. Run the command: `pingall`
7. If no packets are dropped, Jellyfish has been set up successfully
