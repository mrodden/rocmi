# rocmi
Pure Python implementation of ROCm metrics and management interfaces

## usage

`rocmi` is primarily a library module, but can be retrieved via `pip`.

To install `rocmi` locally with its small CLI utility:
```
pip install rocmi[cli]
```

Listing AMDGPU devices:
```
$ rocmi list-devices
+-------+------------------+--------+---------------------------------+-----------------------------+--------------+-----------+
| INDEX | ID               | SERIAL | NAME                            | DRM_PATH                    | BUS_ID       | PROCESSES |
+-------+------------------+--------+---------------------------------+-----------------------------+--------------+-----------+
| 0     | aaaaaaaaaaaaaaaa | None   | Arcturus GL-XL [Instinct MI100] | /sys/class/drm/card0/device | 0000:05:00.0 | []        |
| 1     | bbbbbbbbbbbbbbbb | None   | Arcturus GL-XL [Instinct MI100] | /sys/class/drm/card2/device | 0000:15:00.0 | []        |
| 2     | cccccccccccccccc | None   | Arcturus GL-XL [Instinct MI100] | /sys/class/drm/card1/device | 0000:25:00.0 | []        |
+-------+------------------+--------+---------------------------------+-----------------------------+--------------+-----------+
```
