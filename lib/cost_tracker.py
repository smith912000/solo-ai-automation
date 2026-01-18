"""
Cost Tracker Module

Track token usage and costs across all automations.
Essential for pricing, budgeting, and client billing.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """Pricing for an LLM model (per 1M tokens)."""
    name: str
    input_per_million: float
    output_per_million: float
    
    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for given token usage."""
        input_cost = (tokens_in / 1_000_000) * self.input_per_million
        output_cost = (tokens_out / 1_000_000) * self.output_per_million
        return input_cost + output_cost


# Common model pricing (as of Jan 2024 - update as needed)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": ModelPricing("gpt-4o", 5.00, 15.00),
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", 0.15, 0.60),
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", 10.00, 30.00),
    "gpt-3.5-turbo": ModelPricing("gpt-3.5-turbo", 0.50, 1.50),
    
    # Anthropic
    "claude-3-opus": ModelPricing("claude-3-opus", 15.00, 75.00),
    "claude-3-sonnet": ModelPricing("claude-3-sonnet", 3.00, 15.00),
    "claude-3-haiku": ModelPricing("claude-3-haiku", 0.25, 1.25),
    "claude-3.5-sonnet": ModelPricing("claude-3.5-sonnet", 3.00, 15.00),
    
    # Default fallback
    "default": ModelPricing("default", 5.00, 15.00),
}


@dataclass
class UsageRecord:
    """Single usage record."""
    timestamp: datetime
    automation_name: str
    client_id: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    run_id: Optional[str] = None


@dataclass
class CostSummary:
    """Aggregated cost summary."""
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    total_cost_usd: float = 0.0
    run_count: int = 0
    avg_cost_per_run: float = 0.0
    
    def add(self, tokens_in: int, tokens_out: int, cost: float):
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        self.total_cost_usd += cost
        self.run_count += 1
        self.avg_cost_per_run = self.total_cost_usd / self.run_count if self.run_count > 0 else 0


class CostTracker:
    """
    Track and analyze LLM costs.
    
    Usage:
        tracker = CostTracker()
        cost = tracker.record_usage(
            automation="lead-qualifier",
            client_id="abc123",
            model="gpt-4o",
            tokens_in=500,
            tokens_out=200,
        )
        
        # Get summaries
        daily = tracker.get_daily_summary()
        client = tracker.get_client_summary("abc123")
    """
    
    def __init__(self, db_client=None, budget_limit_usd: Optional[float] = None):
        self.db_client = db_client
        self.budget_limit_usd = budget_limit_usd or float(os.getenv("MONTHLY_BUDGET_USD", "1000"))
        self._records: list[UsageRecord] = []
    
    def get_pricing(self, model: str) -> ModelPricing:
        """Get pricing for a model."""
        return MODEL_PRICING.get(model, MODEL_PRICING["default"])
    
    def calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for given usage."""
        pricing = self.get_pricing(model)
        return pricing.calculate_cost(tokens_in, tokens_out)
    
    def record_usage(
        self,
        automation: str,
        client_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        run_id: Optional[str] = None,
    ) -> float:
        """
        Record token usage and return calculated cost.
        
        Returns:
            Cost in USD
        """
        cost = self.calculate_cost(model, tokens_in, tokens_out)
        
        record = UsageRecord(
            timestamp=datetime.utcnow(),
            automation_name=automation,
            client_id=client_id,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            run_id=run_id,
        )
        
        self._records.append(record)
        
        # Check budget
        self._check_budget_alert()
        
        logger.info(
            f"Recorded usage: {automation}/{client_id} - "
            f"{tokens_in}+{tokens_out} tokens = ${cost:.4f}"
        )
        
        return cost
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> CostSummary:
        """Get cost summary for a day."""
        date = date or datetime.utcnow()
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        summary = CostSummary()
        for record in self._records:
            if start <= record.timestamp < end:
                summary.add(record.tokens_in, record.tokens_out, record.cost_usd)
        
        return summary
    
    def get_client_summary(self, client_id: str, days: int = 30) -> CostSummary:
        """Get cost summary for a client."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        summary = CostSummary()
        for record in self._records:
            if record.client_id == client_id and record.timestamp >= cutoff:
                summary.add(record.tokens_in, record.tokens_out, record.cost_usd)
        
        return summary
    
    def get_automation_summary(self, automation: str, days: int = 30) -> CostSummary:
        """Get cost summary for an automation."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        summary = CostSummary()
        for record in self._records:
            if record.automation_name == automation and record.timestamp >= cutoff:
                summary.add(record.tokens_in, record.tokens_out, record.cost_usd)
        
        return summary
    
    def get_monthly_total(self) -> float:
        """Get total cost for current month."""
        now = datetime.utcnow()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        total = 0.0
        for record in self._records:
            if record.timestamp >= start:
                total += record.cost_usd
        
        return total
    
    def _check_budget_alert(self):
        """Check if approaching budget limit."""
        monthly = self.get_monthly_total()
        
        if monthly >= self.budget_limit_usd:
            logger.critical(f"BUDGET EXCEEDED: ${monthly:.2f} >= ${self.budget_limit_usd:.2f}")
        elif monthly >= self.budget_limit_usd * 0.8:
            logger.warning(f"Budget warning: ${monthly:.2f} (80% of ${self.budget_limit_usd:.2f})")
    
    def estimate_client_margin(
        self,
        client_id: str,
        monthly_price: float,
        days: int = 30,
    ) -> dict:
        """
        Estimate margin for a client.
        
        Returns:
            Dict with revenue, cost, margin, margin_percent
        """
        summary = self.get_client_summary(client_id, days)
        
        # Prorate if less than full period
        if days < 30:
            projected_cost = summary.total_cost_usd * (30 / days)
        else:
            projected_cost = summary.total_cost_usd
        
        margin = monthly_price - projected_cost
        margin_percent = (margin / monthly_price * 100) if monthly_price > 0 else 0
        
        return {
            "revenue": monthly_price,
            "cost": projected_cost,
            "margin": margin,
            "margin_percent": margin_percent,
            "runs": summary.run_count,
            "avg_cost_per_run": summary.avg_cost_per_run,
        }


# Singleton instance
_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
