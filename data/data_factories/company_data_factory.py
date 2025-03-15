import random

from faker import Faker


class CompanyDataFactory:
    """Factory for generating company-related data"""

    def __init__(self, faker: Faker):
        self.faker = faker

    def name(self) -> str:
        """Generate a random company name"""
        return self.faker.company()

    def industry(self) -> str:
        """Generate a random industry"""
        industries = [
            "Aerospace", "Agriculture", "Automotive", "Banking", "Biotechnology",
            "Chemicals", "Construction", "Consumer Goods", "Defense", "Education",
            "Energy", "Entertainment", "Financial Services", "Food & Beverage",
            "Healthcare", "Hospitality", "Information Technology", "Insurance",
            "Legal Services", "Manufacturing", "Media", "Mining", "Pharmaceuticals",
            "Real Estate", "Retail", "Telecommunications", "Transportation", "Utilities"
        ]
        return random.choice(industries)

    def company_type(self) -> str:
        """Generate a random company type"""
        company_types = [
            "LLC", "Inc.", "Corporation", "Ltd.", "LLP", "Partnership", "Sole Proprietorship",
            "S Corporation", "C Corporation", "Non-profit", "B Corporation"
        ]
        return random.choice(company_types)

    def catch_phrase(self) -> str:
        """Generate a random business catch phrase"""
        return self.faker.catch_phrase()

    def bs(self) -> str:
        """Generate a random business statement"""
        return self.faker.bs()