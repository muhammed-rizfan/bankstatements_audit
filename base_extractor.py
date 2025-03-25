from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Callable

class BaseExtractor(ABC):
    """Base class for bank statement extractors"""
    
    @abstractmethod
    def extract_transaction_details(self, description: str, ref_no: str) -> Tuple[str, str]:
        """Extract transaction type and party from description"""
        pass
        
    @abstractmethod
    def extract_transactions(self, text: str, detail_extractor: Callable) -> List[Dict]:
        """Extract transactions from bank statement text"""
        pass 