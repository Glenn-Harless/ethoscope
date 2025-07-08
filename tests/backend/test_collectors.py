from unittest.mock import Mock, patch

import pytest

from backend.etl.collectors.alchemy_collector import AlchemyCollector


@pytest.mark.asyncio
async def test_alchemy_collector():
    """Test Alchemy collector basic functionality"""
    with patch("backend.etl.collectors.alchemy_collector.Web3") as mock_web3:
        # Mock Web3 responses
        mock_instance = Mock()
        mock_web3.return_value = mock_instance
        mock_instance.is_connected.return_value = True
        mock_instance.eth.get_block.return_value = {
            "number": 18000000,
            "timestamp": 1693526400,
            "gasUsed": 15000000,
            "gasLimit": 30000000,
            "transactions": ["0x123", "0x456"],
            "baseFeePerGas": 20000000000,
        }
        mock_instance.eth.gas_price = 25000000000
        mock_instance.eth.get_block_transaction_count.return_value = 150

        collector = AlchemyCollector()
        metrics = await collector.collect()

        assert len(metrics) >= 2
        assert any(m["metric_type"] == "block" for m in metrics)
        assert any(m["metric_type"] == "gas" for m in metrics)
