def test_simple(qitoolchain_action, record_messages):
    foo_tc = qitoolchain_action("create", "foo")
    bar_tc = qitoolchain_action("create", "bar")
    world_package = qitoolchain_action.get_test_package("world")
    qitoolchain_action("add-package", "-c", "foo", "world", world_package)
    record_messages.reset()
    qitoolchain_action("info")
    assert record_messages.find("foo")
    assert record_messages.find("world")
    assert record_messages.find("bar")
    record_messages.reset()
    qitoolchain_action("info", "foo")
    assert record_messages.find("foo")
    assert record_messages.find("world")
    assert not record_messages.find("bar")