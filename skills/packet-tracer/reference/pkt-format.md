# Packet Tracer .pkt file format (as reverse-engineered, verified on PT 8.2.2)

## Container
`.pkt` / `.pka` = XML → zlib (4-byte big-endian length prefix) → XOR `b[i] ^= (len - i)` → Twofish-EAX
(key `137`×16, iv `16`×16, 16-byte tag) → byte-reversed XOR `out[len-1-i] = enc[i] ^ (len - i*len)`.
`scripts/ptcrypto.py -d/-e` does both directions; a decrypt→encrypt round trip is byte-identical.
Logs in `~/pt/logs` use base64 + Twofish-EAX key `186`×16 / iv `190`×16 (`ptcrypto.py -logs`).

## Top level
```
<PACKETTRACER5>
  <VERSION>8.2.0.0000</VERSION>       must be <= installed PT version, else "Incompatible File"
  <NETWORK> <DEVICES> <DEVICE>… </DEVICES> <LINKS> <LINK>… </LINKS> <DESCRIPTION/> </NETWORK>
  <SCENARIOSET> <OPTIONS> <PHYSICALWORKSPACE> <FILTERS> <CLUSTERS> … <GEOVIEW_GRAPHICSITEMS> …
```
A non-empty `NETWORK/DESCRIPTION` pops up a dialog on open. Notes in the logical workspace live in
`PHYSICALWORKSPACE/NOTES/NOTE` (`X`, `Y`, `Z`, `TEXT`, `NOTECLUSTERID=1-1`).

## DEVICE
```
<DEVICE>
  <ENGINE>
    <TYPE customModel="" model="3650-24PS">MultiLayerSwitch</TYPE>   type names: Router, Switch, MultiLayerSwitch, Pc, Server, Printer, Hub, …
    <NAME translate="true">SW1</NAME>  <POWER>true</POWER>
    <MODULE> <SLOT> <MODULE> … <PORT> … </PORT>       nested slots/modules, each PORT = one interface
    <SERIALNUMBER/> <SAVE_REF_ID>save-ref-id:NNN</SAVE_REF_ID>   links reference devices by this id (8.x)
    <SYS_NAME/> <RUNNINGCONFIG> <LINE>…</LINE> </RUNNINGCONFIG>  <STARTUPCONFIG/>   (IOS devices)
    <GATEWAY/> <DNS_CLIENT> …                                                        (end devices)
  </ENGINE>
  <WORKSPACE>
    <LOGICAL> <X/> <Y/> <DEVCLUSTERID>1-1</DEVCLUSTERID> …
    <PHYSICAL>{intercity},{city},{office},{closet},{rack},{device-uuid}</PHYSICAL>
    <PHYSICAL_CPUR> <X/> <Y/> <SLOT/> <SUBSLOT/> <PARENT_PATH>…</PARENT_PATH> <CONTAINER_ID>{rack}</CONTAINER_ID>
  </WORKSPACE>
</DEVICE>
```
PORT fields that matter: `TYPE` (eCopperFastEthernet, eCopperGigabitEthernet, eFiberGigabitEthernet, eSerial…),
`POWER`, `MACADDRESS`/`BIA` (must be unique per file), `IP`, `SUBNET`, `PORT_GATEWAY`, `PORT_DHCP_ENABLE`,
`IPV6_*LINK_LOCAL` (EUI-64 of the MAC), `UP_METHOD` (add `5` if missing).
Interface names are NOT stored on the port; PORT order == order of `interface …` lines in RUNNINGCONFIG.

Every device also needs a `NODE` (TYPE 6, matching `UUID_STR`) under the right container in
`PHYSICALWORKSPACE` (Rack for network gear/servers, Corporate Office for PCs) — otherwise "Invalid File".

## LINK
```
<LINK><TYPE>eCopper</TYPE>                  family: eCopper | eFiber | eSerial | eCoaxial | eOctal | ePhoneLine | eUsb
  <CABLE><LENGTH>1</LENGTH><FUNCTIONAL>true</FUNCTIONAL>
    <FROM>save-ref-id:…</FROM><PORT>GigabitEthernet0/0</PORT><TO>save-ref-id:…</TO><PORT>GigabitEthernet1/0/1</PORT>
    <FROM_DEVICE_MEM_ADDR>0</…> ×4  <GEO_VIEW_COLOR>#000000</GEO_VIEW_COLOR><IS_MANAGED_IN_RACK_VIEW>false</…>
    <TYPE>eStraightThrough</TYPE>           copper only: eStraightThrough | eCrossOver | eRollOver. Fiber/serial: NO inner TYPE
  </CABLE></LINK>
```
PT silently drops a link it considers invalid (e.g. fiber on a copper-only port) — the file still opens.

## Fiber
Only ports that are physically fiber accept `eFiber`. 2960-24TT and 3560-24PS have no SFP slots in PT.
3650-24PS: `GigabitEthernet1/1/1-4` sit in `C3650-SFP-BUILTIN`; the 4 `<SLOT><TYPE>eSfpModule</TYPE></SLOT>`
further down are the SFP cages. Insert `<MODULE><TYPE>eSfpModule</TYPE><MODEL>GLC-LH-SMD</MODEL></MODULE>`
into slot N and set port N's TYPE to `eFiberGigabitEthernet` (this is exactly what PT writes after a GUI drag).
Fiber shows as red/orange lines in the logical view.

## Printer
No Printer-PT in the sample files. A PC-PT becomes a printer by: TYPE text `Printer`, model `Printer-PT`,
remove the second SLOT (eTrs35 audio jacks), remove BLUETOOTH_PORT/BLUETOOTH_MANAGER, USB_PORT_COUNT 0.

## Templates from old files
Devices copied from PT 7.x files need: `POWER` true (some samples are powered off), a `SAVE_REF_ID`,
`UP_METHOD` on ports, and the WORKSPACE block replaced by an 8.2-style one (with SLOT/SUBSLOT/CONTAINER_ID).
Old XML may contain control characters — strip `[\x00-\x08\x0b\x0c\x0e-\x1f]` before parsing.
Some `/opt/pt/saves` files fail with "EAX tag mismatch" (different key) — just use another sample.
