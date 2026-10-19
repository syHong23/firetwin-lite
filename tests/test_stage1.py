from firetwin.kg import check_rules, load_graph, run_query


def test_room_without_smoke_detector_is_found():
    rows = run_query(load_graph(), "rooms_without_smoke_detector")
    assert [label for _, label in rows] == ["Room 103"]


def test_reasoning_infers_sensors():
    assert run_query(load_graph(reason=False), "all_sensors") == []
    assert len(run_query(load_graph(reason=True), "all_sensors")) == 9


def test_shacl_flags_only_room_103():
    conforms, problems = check_rules(load_graph())
    assert not conforms
    assert problems == ["Room103: Room without a smoke detector."]
