"""Stop static analysis CI from silently promoting an untested gameplay release."""
def validate(status,checkpoint):
    if type(status)!=dict or type(checkpoint)!=dict:
        raise ValueError("Status/checkpoint must be JSON objects")
    s=checkpoint.get("port_status")
    if type(s)!=dict or status.get("stage")!="IMPLEMENTATION_INCOMPLETE" or (
        s.get("stage")!="IMPLEMENTATION_INCOMPLETE"):
        raise ValueError("Current project is not a validated gameplay release")
    keys=("full_moddingapi","ready_for_gameplay_test","emulator_tested")
    for origin,record in (("PORT_STATUS",status),("handoff.checkpoint",s)):
        for key in keys:
            if key not in record or record[key] is not False:
                raise ValueError(origin+" cannot claim "+key+" without real Uzuy proof")
    return {"status":"RELEASE_FLAGS_FAIL_CLOSED_STATIC_CI_ONLY",
            "inspected_documents":["PORT_STATUS.json","handoff/checkpoint.json"],
            "full_moddingapi":False,
            "ready_for_gameplay_test":False,
            "emulator_tested":False,
            "runtime_or_Uzuy_evidence_provided":False}
