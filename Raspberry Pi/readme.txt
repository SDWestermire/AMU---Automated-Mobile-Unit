
from lora_comm import LoraComm

# For a remote AMU
remote = LoraComm(role='remote', address=1)
remote.monitor()

# For the base station
base = LoraComm(role='base', address=2)
base.monitor(location_payload="33.6865105 -117.7923516")
