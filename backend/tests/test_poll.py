import pytest
from unittest.mock import patch, MagicMock
from src.scheduler import poll

@patch("src.scheduler.poll.psycopg2.connect")
@patch("src.scheduler.poll.fetch_response")
@patch("src.scheduler.poll.fetch_perplexity_response")
@patch("src.scheduler.poll.fetch_serp_response")
@patch("src.scheduler.poll.analyze_sentiment")
@patch("src.scheduler.poll.extract_insights")
@patch("src.scheduler.poll.send_slack_alert")
def test_poll_main_loop(
    mock_slack, mock_extract, mock_analyze, mock_serp, mock_pplx, mock_gpt, mock_connect
):
    # Simular respuesta de los motores
    mock_gpt.return_value = "Texto generado por GPT"
    mock_pplx.return_value = "Texto generado por Perplexity"
    mock_serp.return_value = [
        {"title": "Título", "snippet": "Snippet", "url": "http://example.com", "source": "example.com"}
    ]
    mock_analyze.return_value = (0.5, "alegría", 0.9)
    mock_extract.return_value = {"brands": [], "competitors": [], "opportunities": [],
                                 "risks": [], "pain_points": [], "trends": [],
                                 "quotes": [], "top_themes": [], "topic_frequency": {},
                                 "source_mentions": {}, "calls_to_action": [],
                                 "audience_targeting": [], "products_or_features": []}

    # Simular cursor y conexión DB
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [(1, "What do people think about Moët & Chandon?")]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    # Ejecutar solo una vez
    poll.main(loop_once=True)

    # Afirmar que todo se llamó
    assert mock_gpt.called
    assert mock_pplx.called
    assert mock_serp.called
    assert mock_analyze.called
    assert mock_extract.called

