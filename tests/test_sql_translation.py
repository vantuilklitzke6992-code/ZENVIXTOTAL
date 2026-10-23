import pytest

from utils.db import _translate_sql


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "SELECT * FROM usuarios WHERE id = ?",
            "SELECT * FROM usuarios WHERE id = %s",
        ),
        (
            "SELECT * FROM usuarios WHERE nome LIKE ?",
            "SELECT * FROM usuarios WHERE nome ILIKE %s",
        ),
        (
            "INSERT OR IGNORE INTO categorias (nome) VALUES (?)",
            "INSERT INTO categorias (nome) VALUES (%s) ON CONFLICT DO NOTHING",
        ),
        (
            "SELECT datetime('now')",
            "SELECT CURRENT_TIMESTAMP",
        ),
        (
            "SELECT datetime('now', '-5 minutes')",
            "SELECT (CURRENT_TIMESTAMP - INTERVAL '5 minutes')",
        ),
        (
            "SELECT * FROM usuarios "
            "WHERE ultimo_acesso >= datetime('now', '-5 minutes')",
            "SELECT * FROM usuarios "
            "WHERE CAST(ultimo_acesso AS TIMESTAMP) >= "
            "(CURRENT_TIMESTAMP - INTERVAL '5 minutes')",
        ),
        (
            "CREATE TABLE exemplo (id INTEGER PRIMARY KEY AUTOINCREMENT)",
            "CREATE TABLE exemplo (id BIGSERIAL PRIMARY KEY)",
        ),
    ],
)
def test_translate_sql_supported_syntax(source, expected):
    assert _translate_sql(source) == expected


def test_translate_sql_preserves_question_marks_in_literals_and_comments():
    source = "SELECT '?' AS literal, id = ? /* ? */ -- ?\n"
    expected = "SELECT '?' AS literal, id = %s /* ? */ -- ?\n"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_like_in_literals():
    source = "SELECT 'LIKE' AS literal, nome LIKE ?"
    expected = "SELECT 'LIKE' AS literal, nome ILIKE %s"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_tokens_in_escaped_string_literal():
    source = "SELECT 'it''s LIKE ? and datetime(''now'')' AS literal, nome LIKE ?"
    expected = "SELECT 'it''s LIKE ? and datetime(''now'')' AS literal, nome ILIKE %s"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_tokens_in_escaped_e_string_literal():
    source = r"SELECT E'it\'s LIKE ? and datetime('now')' AS literal, nome LIKE ?"
    expected = r"SELECT E'it\'s LIKE ? and datetime('now')' AS literal, nome ILIKE %s"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_tokens_in_quoted_identifiers():
    source = 'SELECT "LIKE ? datetime(\'now\')" AS "name?LIKE" FROM usuarios WHERE id = ?'
    expected = 'SELECT "LIKE ? datetime(\'now\')" AS "name?LIKE" FROM usuarios WHERE id = %s'

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_datetime_in_dollar_quoted_literal():
    source = "SELECT $tag$datetime('now')$tag$, datetime('now')"
    expected = "SELECT $tag$datetime('now')$tag$, CURRENT_TIMESTAMP"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_datetime_in_comment():
    source = "SELECT datetime('now') /* datetime('now') */"
    expected = "SELECT CURRENT_TIMESTAMP /* datetime('now') */"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_datetime_in_line_comment():
    source = "SELECT datetime('now') -- datetime('now') ? LIKE\nFROM usuarios"
    expected = "SELECT CURRENT_TIMESTAMP -- datetime('now') ? LIKE\nFROM usuarios"

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_datetime_text_in_quoted_identifier():
    source = 'SELECT "datetime(\'now\')" FROM usuarios WHERE id = ?'
    expected = 'SELECT "datetime(\'now\')" FROM usuarios WHERE id = %s'

    assert _translate_sql(source) == expected


def test_translate_sql_translates_multiple_placeholders_but_preserves_string_marks():
    source = "SELECT '?' AS literal, nome = ?, email = ?, observacao = '??'"
    expected = "SELECT '?' AS literal, nome = %s, email = %s, observacao = '??'"

    assert _translate_sql(source) == expected


def test_translate_sql_other_insert_or_ignore_target_documents_current_limitation():
    """Current behavior drops OR IGNORE, but adds ON CONFLICT only for categorias."""
    source = "INSERT OR IGNORE INTO favoritos (cliente_id) VALUES (?)"
    expected = "INSERT INTO favoritos (cliente_id) VALUES (%s)"

    assert _translate_sql(source) == expected


def test_translate_sql_translates_dates_beside_literals_and_comments():
    source = (
        "SELECT 'datetime(''now'') ?' AS literal, datetime('now') AS criado "
        "/* datetime('now') ? */ FROM usuarios "
        "WHERE ultimo_acesso >= datetime('now', '-5 minutes') "
        "-- datetime('now') ?\nAND id = ? AND email = ?"
    )
    expected = (
        "SELECT 'datetime(''now'') ?' AS literal, CURRENT_TIMESTAMP AS criado "
        "/* datetime('now') ? */ FROM usuarios "
        "WHERE CAST(ultimo_acesso AS TIMESTAMP) >= "
        "(CURRENT_TIMESTAMP - INTERVAL '5 minutes') "
        "-- datetime('now') ?\nAND id = %s AND email = %s"
    )

    assert _translate_sql(source) == expected


def test_translate_sql_preserves_doubled_quotes_nested_comments_and_dollar_literals():
    source = (
        "SELECT 'it''s LIKE ? datetime(''now'')' AS quoted, "
        "$body$LIKE ? datetime('now')$body$ AS dollar "
        "/* outer LIKE ? /* nested datetime('now') */ still ? */ "
        "WHERE id = ?"
    )
    expected = (
        "SELECT 'it''s LIKE ? datetime(''now'')' AS quoted, "
        "$body$LIKE ? datetime('now')$body$ AS dollar "
        "/* outer LIKE ? /* nested datetime('now') */ still ? */ "
        "WHERE id = %s"
    )

    assert _translate_sql(source) == expected
