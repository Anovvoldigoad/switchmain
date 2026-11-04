# NSC ModdingAPI → Switch 1.70

**Implementation in progress. Not full ModdingAPI; not ready for gameplay testing.**
This branch contains source and reproducible component tests. Passing CI does not
mean the game, Android emulators, or complete PC mods have passed testing.

Implemented here: exact-image preflight, bounded condition storage, consistent
PRM/spcload loops, configurable class-selector profiles, and explicit PRM markers
that distinguish API events from native enemy-hide events. Enable/disable control
operations now call native permission writers for all 20 PC selectors. A bounded
CPK converter marks explicitly selected uncompressed PRMs while preserving every
other archive byte. Explicit profiles register up to 32 CPK paths with distinct
priorities; failed registrations remain pending without rebinding accepted IDs.
Condition descriptors now accept appended PC manager records through a validated
profile, with all native entries retained. The profile/PRM packaging tools use
standard Python on Android.

Major remaining work: unsupported MovesetPlus operations, the remaining parameter
families, archive discovery/merge and asynchronous load lifecycle, actor/resource
lifecycle, raw condition-data integration, and gameplay validation. Legacy UJ
membership and several helpers remain Tobi-specific.
The default CPK profile is empty; registration is not proof of completed loading.
Old unmarked PRM assets must not be paired with this branch as a finished package.

- [Continue in a new Chat / Project: checkpoint and explicit MVP prompt](NSC_FULL_API_CONTINUE_CHAT.md)
- [Machine-readable checkpoint](handoff/checkpoint.json)
- [Current status](PORT_STATUS.json)
- [Implementation details and limits](PORTING_PROGRESS.md)
- [Component proof reports](reports/port_foundation/)
- [Reproducible verification workflow](.github/workflows/verify-port-foundation.yml)

CI builds the module with a digest-pinned official devkitPro image and uploads
JSON proof reports only. It does not publish an installable gameplay release.
Historical R181/R183 documents describe their original builds, not acceptance of
this branch as a complete port.
