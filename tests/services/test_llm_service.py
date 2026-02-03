"""
Tests for LLMService - OpenAI integration and SQL generation.

Tests:
- Service initialization
- Prompt building
- Response parsing
- Error handling
- Mocked API interactions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.services.llm_service import LLMService, LLMServiceUnavailableError


class TestServiceInitialization:
    """Tests for LLMService initialization."""

    @patch('backend.app.services.llm_service.settings')
    def test_init_with_api_key(self, mock_settings):
        """Test service initialization with valid API key."""
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.openai_model = "gpt-4"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        mock_settings.use_azure_openai = False  # Ensure we use standard OpenAI

        service = LLMService()

        assert service.client is not None

    @patch('backend.app.services.llm_service.settings')
    def test_init_without_api_key(self, mock_settings):
        """Test service initialization without API key."""
        mock_settings.openai_api_key = None
        mock_settings.use_azure_openai = False

        service = LLMService()

        assert service.client is None


class TestBuildTableSelectionPrompt:
    """Tests for table selection prompt building."""

    def test_build_table_selection_prompt_basic(self):
        """Test building basic table selection prompt."""
        service = LLMService()

        table_names = ["users", "orders", "products"]
        question = "Show me all orders for active users"
        max_tables = 10

        prompt = service._build_table_selection_prompt(table_names, question, max_tables)

        # Check prompt contains all key elements
        assert "users" in prompt
        assert "orders" in prompt
        assert "products" in prompt
        assert "Show me all orders for active users" in prompt
        assert "10" in prompt or "most relevant" in prompt

    def test_build_table_selection_prompt_many_tables(self):
        """Test prompt with many tables."""
        service = LLMService()

        table_names = [f"table_{i}" for i in range(100)]
        question = "Find something"
        max_tables = 5

        prompt = service._build_table_selection_prompt(table_names, question, max_tables)

        # Check that all tables are mentioned
        assert "table_0" in prompt
        assert "table_99" in prompt
        # Check that max_tables is included in prompt
        assert "5" in prompt or "up to 5" in prompt.lower()


class TestParseTableNames:
    """Tests for parsing table names from LLM response."""

    def test_parse_table_names_success(self):
        """Test parsing valid comma-separated table names."""
        service = LLMService()

        table_names = ["users", "orders", "products", "categories"]
        response = "users, orders, products"

        result = service._parse_table_names(response, table_names)

        assert len(result) == 3
        assert "users" in result
        assert "orders" in result
        assert "products" in result

    def test_parse_table_names_with_extra_text(self):
        """Test parsing table names with extra text in response."""
        service = LLMService()

        table_names = ["users", "orders"]
        response = "Based on the question, I recommend: users, orders"

        result = service._parse_table_names(response, table_names)

        assert "users" in result
        assert "orders" in result

    def test_parse_table_names_case_insensitive(self):
        """Test parsing handles case differences."""
        service = LLMService()

        table_names = ["users", "orders"]
        response = "Users, Orders"  # Capitalized

        result = service._parse_table_names(response, table_names)

        assert "users" in result
        assert "orders" in result

    def test_parse_table_names_invalid_tables_filtered(self):
        """Test that invalid table names are filtered out."""
        service = LLMService()

        table_names = ["users", "orders"]
        response = "users, orders, nonexistent_table"

        result = service._parse_table_names(response, table_names)

        assert len(result) == 2
        assert "users" in result
        assert "orders" in result
        assert "nonexistent_table" not in result


class TestExtractSQL:
    """Tests for extracting SQL from LLM response."""

    def test_extract_sql_from_markdown(self):
        """Test extracting SQL from markdown code block."""
        service = LLMService()

        response = """
Here is the query:

```sql
SELECT * FROM users WHERE active = true;
```

This query will show all active users.
"""

        sql = service._extract_sql_from_response(response)

        assert sql == "SELECT * FROM users WHERE active = true;"

    def test_extract_sql_plain_text(self):
        """Test extracting SQL from plain text."""
        service = LLMService()

        response = "SELECT id, name FROM products WHERE price > 100;"

        sql = service._extract_sql_from_response(response)

        assert "SELECT" in sql
        assert "products" in sql

    def test_extract_sql_with_multiline(self):
        """Test extracting multiline SQL."""
        service = LLMService()

        response = """
```sql
SELECT
    u.id,
    u.username,
    COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username;
```
"""

        sql = service._extract_sql_from_response(response)

        assert "SELECT" in sql
        assert "users" in sql
        assert "GROUP BY" in sql

    def test_extract_sql_no_sql_found(self):
        """Test error when no SQL found in response."""
        service = LLMService()

        response = "I cannot generate a query for that question."

        with pytest.raises(ValueError, match="couldn't generate a SQL query"):
            service._extract_sql_from_response(response)

    def test_extract_sql_clarification_response(self):
        """Test handling when LLM asks a clarifying question."""
        service = LLMService()

        response = "Could you please clarify what you mean by 'activities'? Are you looking for today's activities or all activities?"

        # With raise_on_error=True (default), should raise ValueError with the clarification
        with pytest.raises(ValueError, match="Could you please clarify"):
            service._extract_sql_from_response(response)

    def test_extract_sql_no_error_mode(self):
        """Test extract_sql with raise_on_error=False returns tuple."""
        service = LLMService()

        # Test with valid SQL
        response = "SELECT * FROM users;"
        sql, error = service._extract_sql_from_response(response, raise_on_error=False)
        assert sql == "SELECT * FROM users;"
        assert error is None

        # Test with invalid response
        response = "I cannot generate that query."
        sql, error = service._extract_sql_from_response(response, raise_on_error=False)
        assert sql is None
        assert "couldn't generate a SQL query" in error

        # Test with clarification question
        response = "Could you clarify what you mean?"
        sql, error = service._extract_sql_from_response(response, raise_on_error=False)
        assert sql is None
        assert "Could you clarify" in error


class TestSelectRelevantTables:
    """Tests for select_relevant_tables method."""

    @pytest.mark.asyncio
    async def test_select_relevant_tables_no_client(self):
        """Test error when client not configured."""
        service = LLMService()
        service.client = None

        with pytest.raises(LLMServiceUnavailableError, match="not configured"):
            await service.select_relevant_tables(
                table_names=["users", "orders"],
                question="Show all users"
            )

    @pytest.mark.asyncio
    @patch('backend.app.services.llm_service.settings')
    async def test_select_relevant_tables_success(self, mock_settings):
        """Test successful table selection with mocked OpenAI."""
        mock_settings.openai_api_key = "sk-test"
        mock_settings.openai_model = "gpt-4"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        mock_settings.use_azure_openai = False

        service = LLMService()

        # Mock the OpenAI call
        service._call_openai_with_retry = AsyncMock(
            return_value="users, user_sessions, activity_logs"
        )

        table_names = [
            "users", "orders", "products", "user_sessions",
            "activity_logs", "payments"
        ]

        result = await service.select_relevant_tables(
            table_names=table_names,
            question="Show me active users and their recent activity"
        )

        # Should return the tables mentioned in the mocked response
        assert "users" in result or "user_sessions" in result or "activity_logs" in result
        service._call_openai_with_retry.assert_called_once()


class TestGenerateSQL:
    """Tests for generate_sql method."""

    @pytest.mark.asyncio
    async def test_generate_sql_no_client(self):
        """Test error when client not configured."""
        service = LLMService()
        service.client = None

        with pytest.raises(LLMServiceUnavailableError, match="not configured"):
            await service.generate_sql(
                question="Show all users",
                schema_text="Table: users\n  - id (integer)\n  - name (varchar)",
                examples=[]
            )

    @pytest.mark.asyncio
    @patch('backend.app.services.llm_service.settings')
    async def test_generate_sql_success(self, mock_settings):
        """Test successful SQL generation with mocked OpenAI."""
        mock_settings.openai_api_key = "sk-test"
        mock_settings.openai_model = "gpt-4"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        mock_settings.openai_max_tokens = 1000
        mock_settings.openai_temperature = 0.0
        mock_settings.use_azure_openai = False

        service = LLMService()

        # Mock the OpenAI call
        service._call_openai_with_retry = AsyncMock(
            return_value="```sql\nSELECT * FROM users WHERE active = true;\n```"
        )

        schema_text = "Table: users\n  - id (integer)\n  - active (boolean)"
        examples = ["SELECT * FROM users;"]

        result = await service.generate_sql(
            question="Show active users",
            schema_text=schema_text,
            examples=examples
        )

        assert "SELECT" in result
        assert "users" in result
        service._call_openai_with_retry.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.llm_service.settings')
    async def test_generate_sql_invalid_response(self, mock_settings):
        """Test that invalid response triggers clarifying question generation."""
        mock_settings.openai_api_key = "sk-test"
        mock_settings.openai_model = "gpt-4"
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        mock_settings.openai_max_tokens = 1000
        mock_settings.openai_temperature = 0.0
        mock_settings.use_azure_openai = False

        service = LLMService()

        # Mock the OpenAI call with invalid response
        service._call_openai_with_retry = AsyncMock(
            return_value="I cannot help with that."
        )

        # Mock the clarifying question generator
        service._generate_clarifying_question = AsyncMock(
            return_value="What specific user information do you need?"
        )

        with pytest.raises(ValueError, match="What specific user information"):
            await service.generate_sql(
                question="Show users",
                schema_text="Table: users",
                examples=[]
            )

        # Verify clarifying question generator was called
        service._generate_clarifying_question.assert_called_once()


class TestBuildSQLGenerationPrompt:
    """Tests for SQL generation prompt building."""

    def test_build_sql_generation_prompt_with_examples(self):
        """Test building prompt with knowledge base examples."""
        service = LLMService()

        question = "Show active users"
        schema_text = "Table: users\n  - id (integer)\n  - active (boolean)"
        examples = [
            "SELECT * FROM users WHERE active = true;",
            "SELECT id, name FROM users;"
        ]

        prompt = service._build_sql_generation_prompt(question, schema_text, examples)

        assert "Show active users" in prompt
        assert "users" in prompt
        assert "SIMILAR EXAMPLES" in prompt
        assert "SELECT * FROM users WHERE active = true;" in prompt

    def test_build_sql_generation_prompt_without_examples(self):
        """Test building prompt without examples."""
        service = LLMService()

        question = "Count users"
        schema_text = "Table: users"
        examples = []

        prompt = service._build_sql_generation_prompt(question, schema_text, examples)

        assert "Count users" in prompt
        assert "users" in prompt
        assert "SIMILAR EXAMPLES" not in prompt
