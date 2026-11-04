from app.agents import AGENTS, choose_agent


def test_agents_exist():
    assert len(AGENTS) >= 5


def test_agents_have_names():
    for agent in AGENTS:
        assert agent.name
        assert agent.purpose


def test_coding_request_selects_coder():
    result = choose_agent("Python kodu yaz ve program geliştir")
    assert result == "coder"


def test_research_request_selects_researcher():
    result = choose_agent("Bu konu hakkında araştırma yap")
    assert result == "researcher"


def test_writing_request_selects_writer():
    result = choose_agent("Bana bir şiir yaz")
    assert result == "writer"
