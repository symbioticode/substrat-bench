from scripts.omniroute_p0_pilot import extract_content, parse_sse


def test_parse_sse_deltas():
    body = '\n'.join([
        'data: {"choices":[{"delta":{"content":"bon"}}]}',
        'data: {"choices":[{"delta":{"content":"jour"}}]}',
        'data: [DONE]',
    ])
    assert parse_sse(body) == "bonjour"


def test_extract_json_response():
    body = '{"choices":[{"message":{"content":"OK"}}]}'
    assert extract_content(body, "application/json") == "OK"
