"""
Tax Calculator module containing the core tax calculation logic.
This module provides a reusable TaxCalculator class that can be used
by both REST API endpoints and A2A agent executors.
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class TaxCalculator:
    """
    Tax Calculator that provides hardcoded tax calculation results.
    In a real implementation, this would contain actual tax calculation logic.
    """
    
    def __init__(self):
        """Initialize the tax calculator with default tax data."""
        self.tax_data = {
            "federal_tax_rate": 0.22,  # Example: 22% federal tax rate
            "state_tax_rate": 0.05,    # Example: 5% state tax rate
            "effective_tax_rate": 0.27, # Combined rate
            "tax_brackets": [
                {"min": 0, "max": 10000, "rate": 0.10},
                {"min": 10000, "max": 40000, "rate": 0.12},
                {"min": 40000, "max": 85000, "rate": 0.22},
                {"min": 85000, "max": 163300, "rate": 0.24},
                {"min": 163300, "max": 207350, "rate": 0.32},
                {"min": 207350, "max": 518400, "rate": 0.35},
                {"min": 518400, "max": None, "rate": 0.37}
            ],
            "deductions": {
                "standard_deduction": 12950,
                "itemized_deductions": {
                    "mortgage_interest": 0,
                    "property_tax": 0,
                    "charitable_contributions": 0
                }
            },
            "credits": {
                "child_tax_credit": 2000,
                "earned_income_credit": 0
            }
        }
    
    def calculate_tax(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate tax based on the provided context.
        
        Args:
            context: Optional context information (e.g., from decoded JWT token)
        
        Returns:
            Dictionary containing tax calculation results
        """
        logger.info("Performing tax calculations")
        
        # Log context if provided
        if context:
            logger.info(f"Calculation context: {context}")
        
        # In a real implementation, you would use the context to perform
        # personalized tax calculations based on user data, income, etc.
        # For now, we return the hardcoded data
        
        result = {
            "message": "Tax calculations completed",
            "tax_result": self.tax_data.copy()
        }
        
        logger.info("Tax calculations completed successfully")
        return result
    
    def get_tax_brackets(self) -> List[Dict[str, Any]]:
        """Get the current tax brackets."""
        return self.tax_data["tax_brackets"]
    
    def get_tax_rates(self) -> Dict[str, float]:
        """Get the current tax rates."""
        return {
            "federal_tax_rate": self.tax_data["federal_tax_rate"],
            "state_tax_rate": self.tax_data["state_tax_rate"],
            "effective_tax_rate": self.tax_data["effective_tax_rate"]
        }
    
    def get_deductions(self) -> Dict[str, Any]:
        """Get available deductions."""
        return self.tax_data["deductions"]
    
    def get_credits(self) -> Dict[str, Any]:
        """Get available tax credits."""
        return self.tax_data["credits"] 